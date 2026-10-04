#!/usr/bin/env python3
"""
Build ARM64 merge payload and statically patch reference/il2cpp/libil2cpp.so.

Produces:
  dist/arm64-v8a/libil2cpp.so
  dist/arm64-v8a/PATCH_INFO.txt
  dist/arm64-v8a/libil2cpp.so.sha256

Requires: pip install keystone-engine
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

try:
    from keystone import KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN, Ks
except ImportError:
    print("ERROR: keystone-engine required: pip install keystone-engine", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
SRC_SO = ROOT / "reference" / "il2cpp" / "libil2cpp.so"
OUT_DIR = ROOT / "dist" / "arm64-v8a"
OUT_SO = OUT_DIR / "libil2cpp.so"

# --- Snapshot anchors (docs/static_patch_points.md) ---
SET_LOCAL_RVA = 0x1FEB478
# Patch from epilogue (after store inventory to field):
HOOK_RVA = 0x1FEB4E0
# Original epilogue target (logger tail):
ORIG_TAIL_RVA = 0x180423C

# Game helpers
GET_CARD_COUNT = 0x1FEBB60
ADD_CARD = 0x1FEB97C
GET_HERO_COUNT = 0x1FEBBF0
ADD_HERO = 0x1FEBA34  # used to force MethodInfo init for string dict set
# Dictionary<string,int>.set_Item trampoline used by AddHero
HERO_SET_ITEM = 0x265B1FC
# Static MethodInfo* slot for AddHero set_Item (from disasm)
HERO_MI_ADRP = 0x3941000
HERO_MI_OFF = 0xD8
# Init flag byte for AddHero
HERO_INIT_FLAG_ADRP = 0x3C70000
HERO_INIT_FLAG_OFF = 0x897
# il2cpp class/method init helper used by game
IL2CPP_INIT_BL = 0x1804290

IL2CPP_STRING_NEW = 0x0178CC3C

# libc PLT (vaddr)
PLT = {
    "open": 0x03780710,
    "read": 0x037806C0,
    "close": 0x03780720,
    "malloc": 0x037805F0,
    "free": 0x03780600,
    "strlen": 0x037807C0,
    "strtol": 0x03781110,
    "access": 0x03780850,
    "strncmp": 0x03780F50,
    "memset": 0x037801F0,
    "memcpy": 0x03780210,
    "android_log": 0x03780AA0,
}

# ELF: RX segment p_vaddr - p_offset = 0x4000 for this SO
VA_TO_FILE_DELTA = 0x4000

# v3 strategy: extend existing RX PT_LOAD into the 0x4000 VA gap before RW.
# No new program headers — Android/Houdini-safe (v1/v2 extra PT_LOAD broke dlopen).
PAGE = 0x4000
CAVE_SIZE = 0x4000  # exact gap between RX end VA and RW start VA


def va_to_off(va: int) -> int:
    return va - VA_TO_FILE_DELTA


def align_up(n: int, a: int) -> int:
    return (n + a - 1) & ~(a - 1)


def u32(x: int) -> bytes:
    return struct.pack("<I", x & 0xFFFFFFFF)


def encode_branch(pc: int, target: int, link: bool = False) -> bytes:
    """Encode B or BL (imm26)."""
    imm = (target - pc) >> 2
    if imm < -(1 << 25) or imm >= (1 << 25):
        raise ValueError(f"branch out of range pc={pc:#x} target={target:#x}")
    instr = (0x25 if link else 0x05) << 26 | (imm & 0x03FFFFFF)
    return u32(instr)


def build_rodata() -> tuple[bytes, dict[str, int]]:
    """Return rodata blob and name->offset map."""
    parts: list[tuple[str, bytes]] = []

    def add(name: str, s: str | bytes) -> None:
        b = s.encode("utf-8") if isinstance(s, str) else s
        if not b.endswith(b"\x00"):
            b += b"\x00"
        parts.append((name, b))

    add("path0", "/storage/emulated/0/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json")
    add("path1", "/sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json")
    add("path2", "/data/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json")
    add("key_schema", "schemaVersion")
    add("key_cards", "Cards")
    add("key_heroes", "Heroes")
    add("log_tag", "PVZHInvMod")
    add("log_msg", "merge inventory_extra applied")

    blob = bytearray()
    offs: dict[str, int] = {}
    for name, b in parts:
        # 4-byte align
        while len(blob) % 4:
            blob.append(0)
        offs[name] = len(blob)
        blob.extend(b)
    while len(blob) % 16:
        blob.append(0)
    return bytes(blob), offs


def build_payload_asm(code_vaddr: int, ro_vaddr: int, ro_offs: dict[str, int]) -> bytes:
    """
    Assemble full payload at code_vaddr.
    Layout: [hook_epilogue][merge_inventory_extra][helpers] — all in one asm unit with labels.
    """
    def ro(name: str) -> int:
        return ro_vaddr + ro_offs[name]

    # Stack frame for merge: 0x100
    # [sp+0x00] saved x19-x28 pairs + lr/fp
    # locals:
    # We'll use callee-saved extensively.

    asm = f"""
// ===== hook epilogue (entry from SetLocalPlayerInventory @ HOOK_RVA) =====
// On entry: x19 = inventory*, x20 = this+0x18, original frame still open (0x20)
hook_epilogue:
    // nested frame
    sub sp, sp, #0x30
    stp x19, x20, [sp, #0x00]
    stp x21, x30, [sp, #0x10]
    str x22, [sp, #0x20]
    mov x0, x19
    bl merge_inventory_extra
    ldr x22, [sp, #0x20]
    ldp x19, x20, [sp, #0x00]
    // x19=inv, x20=this+0x18 for logger
    mov x0, x20
    mov x1, x19
    ldp x21, x30, [sp, #0x10]
    add sp, sp, #0x30
    // restore original frame & tail to logger
    ldp x20, x19, [sp, #0x10]
    ldp x30, x21, [sp], #0x20
    b {ORIG_TAIL_RVA:#x}

// ===== merge_inventory_extra(x0 = PlayerInventory*) =====
merge_inventory_extra:
    cbz x0, merge_ret
    // prologue: save x19-x28, fp, lr
    stp x29, x30, [sp, #-0x80]!
    mov x29, sp
    stp x19, x20, [sp, #0x10]
    stp x21, x22, [sp, #0x20]
    stp x23, x24, [sp, #0x30]
    stp x25, x26, [sp, #0x40]
    stp x27, x28, [sp, #0x50]
    mov x19, x0                    // inventory
    // cards = *(inv+0x10), heroes = *(inv+0x18)
    ldr x20, [x19, #0x10]
    ldr x21, [x19, #0x18]
    // try open paths
    mov w22, #-1                   // fd
    // path0
    adrp x0, {ro('path0'):#x}
    add x0, x0, #{ro('path0') & 0xFFF:#x}
    bl try_open
    cbnz w0, got_fd
    // path1
    adrp x0, {ro('path1'):#x}
    add x0, x0, #{ro('path1') & 0xFFF:#x}
    bl try_open
    cbnz w0, got_fd
    // path2
    adrp x0, {ro('path2'):#x}
    add x0, x0, #{ro('path2') & 0xFFF:#x}
    bl try_open
    cbnz w0, got_fd
    b merge_epilogue               // no file
got_fd:
    mov w22, w0
    // allocate 256KB+1
    mov x0, #(256*1024+16)
    bl {PLT['malloc']:#x}
    cbz x0, close_and_exit
    mov x23, x0                    // buf
    // read
    mov w0, w22
    mov x1, x23
    mov x2, #(256*1024)
    bl {PLT['read']:#x}
    // close fd
    mov x24, x0                    // nread (ssize)
    mov w0, w22
    bl {PLT['close']:#x}
    mov w22, #-1
    cmp x24, #0
    b.le free_and_exit
    // null-terminate
    mov w8, #0
    strb w8, [x23, x24]
    // strip UTF-8 BOM if present
    mov x0, x23
    bl strip_bom
    mov x23, x0
    // validate schemaVersion == 1
    mov x0, x23
    adrp x1, {ro('key_schema'):#x}
    add x1, x1, #{ro('key_schema') & 0xFFF:#x}
    bl find_key_value
    cbz x0, free_and_exit
    // parse int at x0
    mov x1, xzr                    // endptr unused stack
    mov x2, #10
    // strtol(ptr, NULL, 10)
    mov x1, xzr
    bl {PLT['strtol']:#x}
    cmp x0, #1
    b.ne free_and_exit
    // merge Cards if present
    cbz x20, try_heroes
    mov x0, x23
    adrp x1, {ro('key_cards'):#x}
    add x1, x1, #{ro('key_cards') & 0xFFF:#x}
    bl find_key_value
    cbz x0, try_heroes
    // expect object '{{'
    bl skip_ws_ptr                 // x0 in/out
    ldrb w8, [x0]
    cmp w8, #0x7b                  // '{{'
    b.ne try_heroes
    mov x1, x20                    // cards dict
    mov w2, #0                     // kind=Cards
    bl parse_object_merge
try_heroes:
    cbz x21, free_and_exit
    mov x0, x23
    adrp x1, {ro('key_heroes'):#x}
    add x1, x1, #{ro('key_heroes') & 0xFFF:#x}
    bl find_key_value
    cbz x0, free_and_exit
    bl skip_ws_ptr
    ldrb w8, [x0]
    cmp w8, #0x7b
    b.ne free_and_exit
    mov x1, x21
    mov w2, #1                     // kind=Heroes
    bl parse_object_merge
free_and_exit:
    // free original buffer base: we may have advanced past BOM
    // re-free using saved? For simplicity free x23 always (BOM strip returns same or +3 within block)
    // Actually strip_bom may return buf+3; free must be original malloc ptr.
    // Save malloc base in x25 at alloc time.
    // Fix: use x25 as malloc base
    // --- already used x23 as buf; set x25 at alloc ---
    b free_x25
close_and_exit:
    mov w0, w22
    tbnz w0, #31, merge_epilogue
    bl {PLT['close']:#x}
    b merge_epilogue
free_x25:
    mov x0, x25
    cbz x0, merge_epilogue
    bl {PLT['free']:#x}
merge_epilogue:
    ldp x19, x20, [sp, #0x10]
    ldp x21, x22, [sp, #0x20]
    ldp x23, x24, [sp, #0x30]
    ldp x25, x26, [sp, #0x40]
    ldp x27, x28, [sp, #0x50]
    ldp x29, x30, [sp], #0x80
merge_ret:
    ret

// fix: need x25 = malloc base — patch merge path above via redefinition
// We re-emit alloc section carefully by using x25 from the start in a corrected block.
// (see corrected_merge below if needed)

// ===== try_open(path) -> w0 = fd or 0 on failure =====
// open(path, O_RDONLY=0)
try_open:
    stp x29, x30, [sp, #-0x10]!
    mov x1, xzr                    // O_RDONLY
    bl {PLT['open']:#x}
    // if fd < 0 return 0
    cmp w0, #0
    csel w0, w0, wzr, ge
    // if still negative, zero
    cmp w0, #0
    b.ge try_open_ok
    mov w0, #0
try_open_ok:
    ldp x29, x30, [sp], #0x10
    ret

// ===== strip_bom(x0=buf) -> x0 =====
strip_bom:
    ldrb w8, [x0]
    cmp w8, #0xEF
    b.ne strip_done
    ldrb w8, [x0, #1]
    cmp w8, #0xBB
    b.ne strip_done
    ldrb w8, [x0, #2]
    cmp w8, #0xBF
    b.ne strip_done
    add x0, x0, #3
strip_done:
    ret

// ===== skip_ws_ptr(x0) -> x0 =====
skip_ws_ptr:
skip_ws_loop:
    ldrb w8, [x0]
    cbz w8, skip_ws_done
    cmp w8, #0x20
    b.eq skip_ws_adv
    cmp w8, #0x09
    b.eq skip_ws_adv
    cmp w8, #0x0a
    b.eq skip_ws_adv
    cmp w8, #0x0d
    b.eq skip_ws_adv
    b skip_ws_done
skip_ws_adv:
    add x0, x0, #1
    b skip_ws_loop
skip_ws_done:
    ret

// ===== find_key_value(buf=x0, key=x1) -> x0 value ptr or 0 =====
// Finds "key" then ':' and returns ptr to value (after ws)
find_key_value:
    stp x29, x30, [sp, #-0x40]!
    stp x19, x20, [sp, #0x10]
    stp x21, x22, [sp, #0x20]
    mov x19, x0                    // scan
    mov x20, x1                    // key cstr
    // key len
    mov x0, x20
    bl {PLT['strlen']:#x}
    mov x21, x0                    // klen
find_next:
    // find '"'
    mov x0, x19
find_quote:
    ldrb w8, [x0]
    cbz w8, find_fail
    cmp w8, #0x22                  // '"'
    b.eq quote_found
    add x0, x0, #1
    b find_quote
quote_found:
    add x22, x0, #1                // start of key text
    // strncmp(x22, key, klen)
    mov x0, x22
    mov x1, x20
    mov x2, x21
    bl {PLT['strncmp']:#x}
    cbnz w0, find_advance
    // check closing quote
    ldrb w8, [x22, x21]
    cmp w8, #0x22
    b.ne find_advance
    // after quote
    add x0, x22, x21
    add x0, x0, #1
    bl skip_ws_ptr
    ldrb w8, [x0]
    cmp w8, #0x3a                  // ':'
    b.ne find_advance
    add x0, x0, #1
    bl skip_ws_ptr
    // success x0 = value
    b find_ok
find_advance:
    add x19, x22, #0               // continue after opening quote of this hit
    add x19, x19, #0
    // advance scan past this quote
    mov x19, x22
    b find_next
find_fail:
    mov x0, xzr
find_ok:
    ldp x19, x20, [sp, #0x10]
    ldp x21, x22, [sp, #0x20]
    ldp x29, x30, [sp], #0x40
    ret

// ===== parse_nonneg_int(x0=ptr*) -> w0 value or -1; updates *ptr =====
// In: x0 = char* (by value), Out: w0=val or -1, x1=updated ptr
// Actually we use: in x0=ptr, out w0=val/-1, x1=new ptr
parse_nonneg_int:
    stp x29, x30, [sp, #-0x20]!
    str x19, [sp, #0x10]
    bl skip_ws_ptr
    mov x19, x0
    ldrb w8, [x19]
    cmp w8, #0x30
    b.lt pni_fail
    cmp w8, #0x39
    b.gt pni_fail
    mov w0, #0
pni_loop:
    ldrb w8, [x19]
    cmp w8, #0x30
    b.lt pni_done
    cmp w8, #0x39
    b.gt pni_done
    // w0 = w0*10 + digit
    mov w9, #10
    mul w0, w0, w9
    sub w8, w8, #0x30
    add w0, w0, w8
    add x19, x19, #1
    b pni_loop
pni_done:
    mov x1, x19
    ldr x19, [sp, #0x10]
    ldp x29, x30, [sp], #0x20
    ret
pni_fail:
    mov w0, #-1
    mov x1, x19
    ldr x19, [sp, #0x10]
    ldp x29, x30, [sp], #0x20
    ret

// ===== parse_object_merge(x0='{{'ptr, x1=dict, w2=kind) =====
parse_object_merge:
    stp x29, x30, [sp, #-0x60]!
    stp x19, x20, [sp, #0x10]
    stp x21, x22, [sp, #0x20]
    stp x23, x24, [sp, #0x30]
    stp x25, x26, [sp, #0x40]
    mov x19, x0                    // cursor
    mov x20, x1                    // dict
    mov w21, w2                    // kind
    add x19, x19, #1               // skip '{{'
pom_loop:
    mov x0, x19
    bl skip_ws_ptr
    mov x19, x0
    ldrb w8, [x19]
    cbz w8, pom_done
    cmp w8, #0x7d                  // '}}'
    b.eq pom_done
    cmp w8, #0x2c                  // ','
    b.ne pom_not_comma
    add x19, x19, #1
    b pom_loop
pom_not_comma:
    cmp w8, #0x22                  // '"'
    b.ne pom_done                  // malformed
    add x19, x19, #1
    // copy key into stack buffer [sp+0x50] wait we need more space
    // use [x29- something] — allocate keybuf on stack via extra
    // We'll use a fixed area: at entry we only have 0x60. Expand:
    // Actually reserve 128 bytes by using outer space: rewrite with larger frame.
    // For key: store pointer range [key_start, key_end) and for Cards parse digits;
    // for Heroes, build temp null-terminated on stack (128).
    mov x22, x19                   // key start
pom_key:
    ldrb w8, [x19]
    cbz w8, pom_done
    cmp w8, #0x22
    b.eq pom_key_end
    add x19, x19, #1
    b pom_key
pom_key_end:
    mov x23, x19                   // key end (at closing quote)
    add x19, x19, #1               // past quote
    // key length
    sub x24, x23, x22
    cmp x24, #0
    b.eq pom_done
    cmp x24, #120
    b.gt pom_done
    mov x0, x19
    bl skip_ws_ptr
    mov x19, x0
    ldrb w8, [x19]
    cmp w8, #0x3a
    b.ne pom_done
    add x19, x19, #1
    mov x0, x19
    bl parse_nonneg_int
    cmp w0, #0
    b.lt pom_done
    mov w25, w0                    // value
    mov x19, x1                    // updated ptr
    // branch kind
    cbnz w21, pom_hero
    // Cards: parse key digits to int
    mov x0, x22
    mov x1, x24
    bl parse_digits_key            // w0=id or -1
    cmp w0, #0
    b.lt pom_loop_continue
    mov w26, w0                    // card id
    // merge card: need cards dict x20
    cbz x20, pom_loop_continue
    mov w0, w26
    mov x1, x20
    bl {GET_CARD_COUNT:#x}
    mov w27, w0                    // existing
    cmp w25, w27
    b.le pom_loop_continue
    sub w2, w25, w27
    mov w0, w26
    mov x1, x20
    // w2 = delta already
    bl {ADD_CARD:#x}
    b pom_loop_continue
pom_hero:
    cbz x20, pom_loop_continue
    // build C string on stack
    sub sp, sp, #0x80
    mov x0, sp
    mov x1, x22
    mov x2, x24
    bl {PLT['memcpy']:#x}
    mov w8, #0
    strb w8, [sp, x24]
    // il2cpp_string_new
    mov x0, sp
    bl {IL2CPP_STRING_NEW:#x}
    add sp, sp, #0x80
    cbz x0, pom_loop_continue
    mov x26, x0                    // managed string
    // get existing
    mov x0, x26
    mov x1, x20
    bl {GET_HERO_COUNT:#x}
    mov w27, w0
    cmp w25, w27
    b.le pom_loop_continue
    // set heroes[str] = extra via MethodInfo path
    mov x0, x20                    // dict
    mov x1, x26                    // key str
    mov w2, w25                    // value
    bl heroes_dict_set
pom_loop_continue:
    b pom_loop
pom_done:
    ldp x19, x20, [sp, #0x10]
    ldp x21, x22, [sp, #0x20]
    ldp x23, x24, [sp, #0x30]
    ldp x25, x26, [sp, #0x40]
    ldp x29, x30, [sp], #0x60
    ret

// ===== parse_digits_key(x0=ptr, x1=len) -> w0 id or -1 =====
parse_digits_key:
    cbz x1, pdk_fail
    mov w0, #0
pdk_loop:
    cbz x1, pdk_ok
    ldrb w8, [x0]
    cmp w8, #0x30
    b.lt pdk_fail
    cmp w8, #0x39
    b.gt pdk_fail
    mov w9, #10
    mul w0, w0, w9
    sub w8, w8, #0x30
    add w0, w0, w8
    add x0, x0, #1
    sub x1, x1, #1
    b pdk_loop
pdk_ok:
    ret
pdk_fail:
    mov w0, #-1
    ret

// ===== heroes_dict_set(x0=dict, x1=str, w2=value) =====
// Ensures AddHero MethodInfo inited, then Dictionary.set_Item
heroes_dict_set:
    stp x29, x30, [sp, #-0x30]!
    stp x19, x20, [sp, #0x10]
    str x21, [sp, #0x20]
    mov x19, x0
    mov x20, x1
    mov w21, w2
    cbz x19, hds_done
    cbz x20, hds_done
    // init flag
    adrp x8, {HERO_INIT_FLAG_ADRP:#x}
    add x8, x8, #{HERO_INIT_FLAG_OFF:#x}
    ldrb w9, [x8]
    tbnz w9, #0, hds_inited
    // init MethodInfo (same as AddHero)
    adrp x0, {HERO_MI_ADRP:#x}
    add x0, x0, #{HERO_MI_OFF:#x}
    ldr x0, [x0]
    bl {IL2CPP_INIT_BL:#x}
    adrp x8, {HERO_INIT_FLAG_ADRP:#x}
    add x8, x8, #{HERO_INIT_FLAG_OFF:#x}
    mov w9, #1
    strb w9, [x8]
hds_inited:
    adrp x8, {HERO_MI_ADRP:#x}
    add x8, x8, #{HERO_MI_OFF:#x}
    ldr x8, [x8]
    cbz x8, hds_done
    ldr x3, [x8]                   // MethodInfo*
    cbz x3, hds_done
    mov x0, x19
    mov x1, x20
    mov w2, w21
    bl {HERO_SET_ITEM:#x}
hds_done:
    ldr x21, [sp, #0x20]
    ldp x19, x20, [sp, #0x10]
    ldp x29, x30, [sp], #0x30
    ret
"""

    # Fix malloc base tracking: rewrite alloc section by post-processing is hard.
    # Instead inject a corrected prologue sequence via second asm patch.
    # We'll fix in a cleaner full rewrite of merge_inventory_extra alloc part.

    ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    try:
        enc, count = ks.asm(asm, code_vaddr)
    except Exception as e:
        # Keystone sometimes gives limited error info; write asm for debug
        debug_path = OUT_DIR / "payload_debug.S"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(asm, encoding="utf-8")
        raise RuntimeError(f"Keystone failed: {e}. Wrote {debug_path}") from e
    if enc is None:
        raise RuntimeError("Keystone returned None")
    code = bytes(enc)
    return code


def build_payload_asm_v2(code_vaddr: int, ro_vaddr: int, ro_offs: dict[str, int]) -> bytes:
    """Corrected payload with x25 = malloc base."""

    def ro(name: str) -> int:
        return ro_vaddr + ro_offs[name]

    # ADRP page for each ro symbol must be correct: adrp targets page of address.
    # Keystone handles `adrp x0, imm` when given absolute label via immediate.
    # Using `adrp x0, #addr` + `add x0, x0, #lo12` — keystone syntax:
    #   adrp x0, 0x4001000
    #   add  x0, x0, #0x123
    # Note: ADRP immediate is page-aligned; add uses low 12 bits.

    def load_ro(reg: str, name: str) -> str:
        addr = ro(name)
        page = addr & ~0xFFF
        off = addr & 0xFFF
        return f"    adrp {reg}, {page:#x}\n    add {reg}, {reg}, #{off:#x}\n"

    asm = []
    A = asm.append

    A(f"""
hook_epilogue:
    sub sp, sp, #0x30
    stp x19, x20, [sp, #0x00]
    stp x21, x30, [sp, #0x10]
    str x22, [sp, #0x20]
    mov x0, x19
    bl merge_inventory_extra
    ldr x22, [sp, #0x20]
    ldp x19, x20, [sp, #0x00]
    mov x0, x20
    mov x1, x19
    ldp x21, x30, [sp, #0x10]
    add sp, sp, #0x30
    ldp x20, x19, [sp, #0x10]
    ldp x30, x21, [sp], #0x20
    b {ORIG_TAIL_RVA:#x}

merge_inventory_extra:
    cbz x0, merge_ret_early
    stp x29, x30, [sp, #-0x80]!
    mov x29, sp
    stp x19, x20, [sp, #0x10]
    stp x21, x22, [sp, #0x20]
    stp x23, x24, [sp, #0x30]
    stp x25, x26, [sp, #0x40]
    stp x27, x28, [sp, #0x50]
    mov x19, x0
    ldr x20, [x19, #0x10]
    ldr x21, [x19, #0x18]
    mov x25, xzr
    mov w22, wzr
""")
    # try paths
    for i, pname in enumerate(("path0", "path1", "path2")):
        A(load_ro("x0", pname))
        A("    bl try_open\n")
        A("    cbnz w0, got_fd\n")
    A("""
    b merge_epilogue
got_fd:
    mov w22, w0
    // malloc 256KiB (room for NUL at end after reading max 256KiB-1)
    mov x0, #262144
    bl """ + f"{PLT['malloc']:#x}" + """
    cbz x0, close_fail
    mov x25, x0
    mov x23, x0
    mov w0, w22
    mov x1, x23
    mov x2, #262143
    bl """ + f"{PLT['read']:#x}" + """
    mov x24, x0
    mov w0, w22
    bl """ + f"{PLT['close']:#x}" + """
    mov w22, wzr
    cmp x24, #0
    b.le merge_epilogue
    mov w8, #0
    strb w8, [x23, x24]
    mov x0, x23
    bl strip_bom
    mov x23, x0
""")
    A(load_ro("x1", "key_schema"))
    A("""
    mov x0, x23
    bl find_key_value
    cbz x0, merge_epilogue
    mov x1, xzr
    mov x2, #10
    bl """ + f"{PLT['strtol']:#x}" + """
    cmp x0, #1
    b.ne merge_epilogue
    cbz x20, do_heroes
""")
    A(load_ro("x1", "key_cards"))
    A("""
    mov x0, x23
    bl find_key_value
    cbz x0, do_heroes
    bl skip_ws_ptr
    ldrb w8, [x0]
    cmp w8, #0x7b
    b.ne do_heroes
    mov x1, x20
    mov w2, #0
    bl parse_object_merge
do_heroes:
    cbz x21, merge_epilogue
""")
    A(load_ro("x1", "key_heroes"))
    A("""
    mov x0, x23
    bl find_key_value
    cbz x0, merge_epilogue
    bl skip_ws_ptr
    ldrb w8, [x0]
    cmp w8, #0x7b
    b.ne merge_epilogue
    mov x1, x21
    mov w2, #1
    bl parse_object_merge
    b merge_epilogue
close_fail:
    mov w0, w22
    cmp w0, #0
    b.le merge_epilogue
    bl """ + f"{PLT['close']:#x}" + """
merge_epilogue:
    mov x0, x25
    cbz x0, merge_restore
    bl """ + f"{PLT['free']:#x}" + """
merge_restore:
    ldp x19, x20, [sp, #0x10]
    ldp x21, x22, [sp, #0x20]
    ldp x23, x24, [sp, #0x30]
    ldp x25, x26, [sp, #0x40]
    ldp x27, x28, [sp, #0x50]
    ldp x29, x30, [sp], #0x80
merge_ret_early:
    ret

try_open:
    stp x29, x30, [sp, #-0x10]!
    mov x1, xzr
    bl """ + f"{PLT['open']:#x}" + """
    cmp w0, #0
    b.ge try_open_ret
    mov w0, #0
try_open_ret:
    ldp x29, x30, [sp], #0x10
    ret

strip_bom:
    ldrb w8, [x0]
    cmp w8, #0xEF
    b.ne strip_done
    ldrb w8, [x0, #1]
    cmp w8, #0xBB
    b.ne strip_done
    ldrb w8, [x0, #2]
    cmp w8, #0xBF
    b.ne strip_done
    add x0, x0, #3
strip_done:
    ret

skip_ws_ptr:
skip_ws_loop:
    ldrb w8, [x0]
    cbz w8, skip_ws_done
    cmp w8, #0x20
    b.eq skip_ws_adv
    cmp w8, #0x09
    b.eq skip_ws_adv
    cmp w8, #0x0a
    b.eq skip_ws_adv
    cmp w8, #0x0d
    b.eq skip_ws_adv
    b skip_ws_done
skip_ws_adv:
    add x0, x0, #1
    b skip_ws_loop
skip_ws_done:
    ret

find_key_value:
    stp x29, x30, [sp, #-0x40]!
    stp x19, x20, [sp, #0x10]
    stp x21, x22, [sp, #0x20]
    mov x19, x0
    mov x20, x1
    mov x0, x20
    bl """ + f"{PLT['strlen']:#x}" + """
    mov x21, x0
find_next:
    mov x0, x19
find_quote:
    ldrb w8, [x0]
    cbz w8, find_fail
    cmp w8, #0x22
    b.eq quote_found
    add x0, x0, #1
    b find_quote
quote_found:
    add x22, x0, #1
    mov x0, x22
    mov x1, x20
    mov x2, x21
    bl """ + f"{PLT['strncmp']:#x}" + """
    cbnz w0, find_advance
    ldrb w8, [x22, x21]
    cmp w8, #0x22
    b.ne find_advance
    add x0, x22, x21
    add x0, x0, #1
    bl skip_ws_ptr
    ldrb w8, [x0]
    cmp w8, #0x3a
    b.ne find_advance
    add x0, x0, #1
    bl skip_ws_ptr
    b find_ok
find_advance:
    mov x19, x22
    b find_next
find_fail:
    mov x0, xzr
find_ok:
    ldp x19, x20, [sp, #0x10]
    ldp x21, x22, [sp, #0x20]
    ldp x29, x30, [sp], #0x40
    ret

parse_nonneg_int:
    stp x29, x30, [sp, #-0x20]!
    str x19, [sp, #0x10]
    bl skip_ws_ptr
    mov x19, x0
    ldrb w8, [x19]
    cmp w8, #0x30
    b.lt pni_fail
    cmp w8, #0x39
    b.gt pni_fail
    mov w0, #0
pni_loop:
    ldrb w8, [x19]
    cmp w8, #0x30
    b.lt pni_done
    cmp w8, #0x39
    b.gt pni_done
    mov w9, #10
    mul w0, w0, w9
    sub w8, w8, #0x30
    add w0, w0, w8
    add x19, x19, #1
    b pni_loop
pni_done:
    mov x1, x19
    ldr x19, [sp, #0x10]
    ldp x29, x30, [sp], #0x20
    ret
pni_fail:
    mov w0, #0xffffffff
    mov x1, x19
    ldr x19, [sp, #0x10]
    ldp x29, x30, [sp], #0x20
    ret

parse_object_merge:
    // Save full callee-saved set used below (x19-x28)
    stp x29, x30, [sp, #-0x70]!
    stp x19, x20, [sp, #0x10]
    stp x21, x22, [sp, #0x20]
    stp x23, x24, [sp, #0x30]
    stp x25, x26, [sp, #0x40]
    stp x27, x28, [sp, #0x50]
    mov x19, x0
    mov x20, x1
    mov w21, w2
    add x19, x19, #1
pom_loop:
    mov x0, x19
    bl skip_ws_ptr
    mov x19, x0
    ldrb w8, [x19]
    cbz w8, pom_done
    cmp w8, #0x7d
    b.eq pom_done
    cmp w8, #0x2c
    b.ne pom_not_comma
    add x19, x19, #1
    b pom_loop
pom_not_comma:
    cmp w8, #0x22
    b.ne pom_done
    add x19, x19, #1
    mov x22, x19
pom_key:
    ldrb w8, [x19]
    cbz w8, pom_done
    cmp w8, #0x22
    b.eq pom_key_end
    add x19, x19, #1
    b pom_key
pom_key_end:
    mov x23, x19
    add x19, x19, #1
    sub x24, x23, x22
    cmp x24, #0
    b.eq pom_done
    cmp x24, #120
    b.gt pom_done
    mov x0, x19
    bl skip_ws_ptr
    mov x19, x0
    ldrb w8, [x19]
    cmp w8, #0x3a
    b.ne pom_done
    add x19, x19, #1
    mov x0, x19
    bl parse_nonneg_int
    // accept 0 as value; only reject <0 (0xffffffff)
    cmn w0, #1
    b.eq pom_done
    mov w25, w0
    mov x19, x1
    cbnz w21, pom_hero
    // ---- Cards path ----
    mov x0, x22
    mov x1, x24
    bl parse_digits_key
    cmn w0, #1
    b.eq pom_loop
    mov w26, w0
    cbz x20, pom_loop
    // Guard: dict must look like a managed object (non-null klass ptr)
    ldr x8, [x20]
    cbz x8, pom_loop
    // Prefer max merge via GetCount + Add(delta). MethodInfo arg is NULL
    // (matches game call sites that pass x3=xzr into these helpers).
    mov w0, w26
    mov x1, x20
    mov x2, xzr
    bl """ + f"{GET_CARD_COUNT:#x}" + """
    mov w27, w0
    // If GetCount failed weirdly (negative), treat as 0
    cmp w27, #0
    csel w27, w27, wzr, ge
    cmp w25, w27
    b.le pom_loop
    sub w2, w25, w27
    // quantity must be > 0
    cmp w2, #0
    b.le pom_loop
    mov w0, w26
    mov x1, x20
    mov x3, xzr
    bl """ + f"{ADD_CARD:#x}" + """
    b pom_loop
pom_hero:
    // Heroes optional; skip on any doubt
    cbz x20, pom_loop
    ldr x8, [x20]
    cbz x8, pom_loop
    sub sp, sp, #0x80
    mov x0, sp
    mov x1, x22
    mov x2, x24
    bl """ + f"{PLT['memcpy']:#x}" + """
    mov w8, #0
    mov x9, sp
    strb w8, [x9, x24]
    mov x0, sp
    bl """ + f"{IL2CPP_STRING_NEW:#x}" + """
    add sp, sp, #0x80
    cbz x0, pom_loop
    mov x26, x0
    mov x0, x26
    mov x1, x20
    mov x2, xzr
    bl """ + f"{GET_HERO_COUNT:#x}" + """
    mov w27, w0
    cmp w25, w27
    b.le pom_loop
    mov x0, x20
    mov x1, x26
    mov w2, w25
    bl heroes_dict_set
    b pom_loop
pom_done:
    ldp x19, x20, [sp, #0x10]
    ldp x21, x22, [sp, #0x20]
    ldp x23, x24, [sp, #0x30]
    ldp x25, x26, [sp, #0x40]
    ldp x27, x28, [sp, #0x50]
    ldp x29, x30, [sp], #0x70
    ret

parse_digits_key:
    cbz x1, pdk_fail
    mov w0, #0
pdk_loop:
    cbz x1, pdk_ok
    ldrb w8, [x0]
    cmp w8, #0x30
    b.lt pdk_fail
    cmp w8, #0x39
    b.gt pdk_fail
    mov w9, #10
    mul w0, w0, w9
    sub w8, w8, #0x30
    add w0, w0, w8
    add x0, x0, #1
    sub x1, x1, #1
    b pdk_loop
pdk_ok:
    ret
pdk_fail:
    mov w0, #0xffffffff
    ret

heroes_dict_set:
    stp x29, x30, [sp, #-0x30]!
    stp x19, x20, [sp, #0x10]
    str x21, [sp, #0x20]
    mov x19, x0
    mov x20, x1
    mov w21, w2
    cbz x19, hds_done
    cbz x20, hds_done
    adrp x8, """ + f"{HERO_INIT_FLAG_ADRP:#x}" + """
    add x8, x8, #""" + f"{HERO_INIT_FLAG_OFF:#x}" + """
    ldrb w9, [x8]
    tbnz w9, #0, hds_inited
    adrp x0, """ + f"{HERO_MI_ADRP:#x}" + """
    add x0, x0, #""" + f"{HERO_MI_OFF:#x}" + """
    ldr x0, [x0]
    bl """ + f"{IL2CPP_INIT_BL:#x}" + """
    adrp x8, """ + f"{HERO_INIT_FLAG_ADRP:#x}" + """
    add x8, x8, #""" + f"{HERO_INIT_FLAG_OFF:#x}" + """
    mov w9, #1
    strb w9, [x8]
hds_inited:
    adrp x8, """ + f"{HERO_MI_ADRP:#x}" + """
    add x8, x8, #""" + f"{HERO_MI_OFF:#x}" + """
    ldr x8, [x8]
    cbz x8, hds_done
    ldr x3, [x8]
    cbz x3, hds_done
    mov x0, x19
    mov x1, x20
    mov w2, w21
    bl """ + f"{HERO_SET_ITEM:#x}" + """
hds_done:
    ldr x21, [sp, #0x20]
    ldp x19, x20, [sp, #0x10]
    ldp x29, x30, [sp], #0x30
    ret
""")

    text = "\n".join(asm)
    ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    try:
        enc, count = ks.asm(text, code_vaddr)
    except Exception as e:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "payload_debug.S").write_text(text, encoding="utf-8")
        raise RuntimeError(f"Keystone failed: {e}") from e
    print(f"  payload code: {len(enc)} bytes, {count} instructions")
    return bytes(enc)


def _find_rx_load(so: bytes, e_phoff: int, e_phnum: int, e_phentsize: int) -> tuple[int, int, int, int]:
    """Return (phdr_index, p_offset, p_vaddr, p_filesz) for the executable LOAD that holds HOOK_RVA."""
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type, p_flags = struct.unpack_from("<II", so, o)
        if p_type != 1 or not (p_flags & 1):  # PT_LOAD + X
            continue
        p_offset, p_vaddr, _, p_filesz, p_memsz, _ = struct.unpack_from("<6Q", so, o + 8)
        if p_vaddr <= HOOK_RVA < p_vaddr + p_memsz:
            return i, p_offset, p_vaddr, p_filesz
    raise RuntimeError("RX LOAD containing hook not found")


def patch_elf_extend_rx(so: bytearray, payload: bytes) -> dict:
    """
    v3: Insert payload into the 16KiB VA gap between RX and RW by:
      - inserting CAVE_SIZE bytes at the end of the RX LOAD in the file
      - growing that LOAD's filesz/memsz
      - shifting p_offset of all later program headers
      - shifting sh_offset of all section headers past the insert point
        (critical on real Android bionic: PT_DYNAMIC must match .dynamic)

    This avoids Houdini/Android failures seen with extra PT_LOAD + relocated PHDR
    (dlopen: undefined symbol JNI_OnLoad), and the real-device rejection:
      .dynamic section has invalid offset ... expected to match PT_DYNAMIC
    """
    if so[:4] != b"\x7fELF":
        raise ValueError("not ELF")
    if len(payload) > CAVE_SIZE:
        raise ValueError(f"payload {len(payload)} > cave {CAVE_SIZE}")

    e_phoff = struct.unpack_from("<Q", so, 32)[0]
    e_shoff = struct.unpack_from("<Q", so, 40)[0]
    e_phentsize = struct.unpack_from("<H", so, 54)[0]
    e_phnum = struct.unpack_from("<H", so, 56)[0]
    e_shentsize = struct.unpack_from("<H", so, 58)[0]
    e_shnum = struct.unpack_from("<H", so, 60)[0]
    if e_phentsize != 56:
        raise ValueError(f"unexpected e_phentsize {e_phentsize}")
    if e_shentsize != 64:
        raise ValueError(f"unexpected e_shentsize {e_shentsize}")

    rx_i, rx_off, rx_va, rx_filesz = _find_rx_load(so, e_phoff, e_phnum, e_phentsize)
    insert_at = rx_off + rx_filesz
    code_vaddr = rx_va + rx_filesz  # first free VA in the gap

    # Confirm next LOAD starts at insert_at (contiguous file layout)
    next_load_off = None
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type = struct.unpack_from("<I", so, o)[0]
        if p_type != 1:
            continue
        p_offset = struct.unpack_from("<Q", so, o + 8)[0]
        if p_offset >= insert_at:
            if next_load_off is None or p_offset < next_load_off:
                next_load_off = p_offset
    if next_load_off != insert_at:
        print(f"WARN: next LOAD off {next_load_off:#x} != RX end {insert_at:#x}")

    # Build cave (payload + zero pad)
    cave = bytearray(CAVE_SIZE)
    cave[0 : len(payload)] = payload

    # Insert into file
    so[insert_at:insert_at] = cave

    # Shift e_shoff if section headers live after insert point
    new_shoff = e_shoff
    if e_shoff >= insert_at:
        new_shoff = e_shoff + CAVE_SIZE
        struct.pack_into("<Q", so, 40, new_shoff)

    # Update program headers (still at original e_phoff — before insert, so OK)
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type = struct.unpack_from("<I", so, o)[0]
        p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = struct.unpack_from(
            "<6Q", so, o + 8
        )
        if i == rx_i:
            # Grow RX
            struct.pack_into("<Q", so, o + 32, p_filesz + CAVE_SIZE)  # filesz
            struct.pack_into("<Q", so, o + 40, p_memsz + CAVE_SIZE)  # memsz
            continue
        if p_offset >= insert_at and p_type != 0:
            # Shift file offset; vaddr unchanged
            struct.pack_into("<Q", so, o + 8, p_offset + CAVE_SIZE)

    # Update section headers (SHT lives at new_shoff). Real Android bionic compares
    # PT_DYNAMIC.p_offset against SHT .dynamic.sh_offset and aborts if they differ.
    # ELF64_Shdr: name(4) type(4) flags(8) addr(8) offset(8) size(8) ...
    sh_shifted = 0
    if e_shnum > 0 and new_shoff + e_shnum * e_shentsize <= len(so):
        for i in range(e_shnum):
            o = new_shoff + i * e_shentsize
            sh_offset = struct.unpack_from("<Q", so, o + 24)[0]
            if sh_offset >= insert_at:
                struct.pack_into("<Q", so, o + 24, sh_offset + CAVE_SIZE)
                sh_shifted += 1
        print(f"  section headers shifted: {sh_shifted}/{e_shnum} (e_shoff={new_shoff:#x})")
    else:
        print("WARN: section header table missing or out of range; PT_DYNAMIC/.dynamic may mismatch")

    # Hook: after insert, file offsets for RX content before insert_at are unchanged
    hook_off = va_to_off(HOOK_RVA)
    orig = bytes(so[hook_off : hook_off + 20])
    expected_start = bytes.fromhex("e00314aa")  # mov x0, x20
    if orig[:4] != expected_start:
        print(f"WARN: hook site bytes unexpected: {orig[:4].hex()} (expected {expected_start.hex()})")
    branch = encode_branch(HOOK_RVA, code_vaddr, link=False)
    nop = u32(0xD503201F)
    so[hook_off : hook_off + 20] = branch + nop * 4

    # Sanity: RX now ends at RW start VA
    o = e_phoff + rx_i * e_phentsize
    new_filesz = struct.unpack_from("<Q", so, o + 32)[0]
    new_memsz = struct.unpack_from("<Q", so, o + 40)[0]
    rx_end_va = rx_va + new_memsz
    print(f"  RX extended: filesz/memsz +{CAVE_SIZE:#x} -> end VA {rx_end_va:#x}")
    print(f"  payload at VA {code_vaddr:#x} file {insert_at:#x} ({len(payload)} bytes)")

    return {
        "strategy": "v3_extend_rx_cave",
        "code_vaddr": code_vaddr,
        "cave_file_off": insert_at,
        "cave_size": CAVE_SIZE,
        "payload_size": len(payload),
        "rx_phdr_index": rx_i,
        "rx_new_filesz": new_filesz,
        "rx_new_memsz": new_memsz,
        "rx_end_va": rx_end_va,
        "hook_rva": HOOK_RVA,
        "hook_file_off": hook_off,
        "orig_epilogue_bytes": orig.hex(),
        "branch_bytes": branch.hex(),
        "e_phoff_unchanged": e_phoff,
        "e_phnum_unchanged": e_phnum,
        "sh_headers_shifted": sh_shifted if e_shnum > 0 else 0,
        "fix_note": (
            "No new PT_LOAD; PHDR table not relocated; section sh_offset shifted "
            "to keep PT_DYNAMIC/.dynamic in sync (bionic-safe)"
        ),
    }


def main() -> int:
    if not SRC_SO.is_file():
        print(f"ERROR: missing {SRC_SO}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Discover RX end VA from source SO for correct assemble base
    so_probe = SRC_SO.read_bytes()
    e_phoff = struct.unpack_from("<Q", so_probe, 32)[0]
    e_phentsize = struct.unpack_from("<H", so_probe, 54)[0]
    e_phnum = struct.unpack_from("<H", so_probe, 56)[0]
    _, rx_off, rx_va, rx_filesz = _find_rx_load(so_probe, e_phoff, e_phnum, e_phentsize)
    code_vaddr = rx_va + rx_filesz

    # Use simplified payload (device-proven open/read/AddCard path).
    # Complex GetCardInventoryCount+JSON path crashed under Houdini; see build_payload_simple.py.
    from build_payload_simple import build_full as build_simple_payload

    payload, path_va = build_simple_payload(code_vaddr)
    if len(payload) > CAVE_SIZE:
        print(f"ERROR: payload {len(payload)} exceeds cave {CAVE_SIZE}", file=sys.stderr)
        return 1

    print(f"  code VA: {code_vaddr:#x}")
    print(f"  path VA: {path_va:#x}")
    print(f"  total payload: {len(payload)} bytes / cave {CAVE_SIZE:#x}")
    ro_offs = {"path0": path_va - code_vaddr}
    ro_vaddr = path_va
    so = bytearray(SRC_SO.read_bytes())
    orig_hash = hashlib.sha256(so).hexdigest()
    info = patch_elf_extend_rx(so, bytes(payload))
    _validate_patched_v3(so, info)
    OUT_SO.write_bytes(so)
    new_hash = hashlib.sha256(so).hexdigest()

    (ROOT / "dist" / "libil2cpp.so").write_bytes(so)
    (ROOT / "dist" / "libil2cpp.so.sha256").write_text(new_hash + "\n", encoding="utf-8")

    # JSON-friendly copy (ints → hex strings where useful)
    report = dict(info)
    report.update(
        {
            "source_so": str(SRC_SO.relative_to(ROOT)),
            "output_so": str(OUT_SO.relative_to(ROOT)),
            "abi": "arm64-v8a",
            "set_local_rva": hex(SET_LOCAL_RVA),
            "orig_sha256": orig_hash,
            "patched_sha256": new_hash,
            "orig_size": SRC_SO.stat().st_size,
            "patched_size": len(so),
            "rodata_offs": ro_offs,
            "ro_vaddr": hex(ro_vaddr),
            "code_vaddr": hex(code_vaddr),
            "cave_file_off": hex(info["cave_file_off"]),
            "rx_end_va": hex(info["rx_end_va"]),
            "hook_rva": hex(HOOK_RVA),
            "crash_fix": "v3b: RX cave + simple JSON scan + AddCard only (no GetCount)",
            "payload_variant": "build_payload_simple",
        }
    )

    (OUT_DIR / "libil2cpp.so.sha256").write_text(new_hash + "\n", encoding="utf-8")
    (OUT_DIR / "PATCH_INFO.txt").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "payload.bin").write_bytes(payload)

    print(f"OK: wrote {OUT_SO}")
    print(f"    sha256={new_hash}")
    print(f"    size {report['orig_size']} -> {report['patched_size']}")
    print(f"    hook @{HOOK_RVA:#x} -> code @{code_vaddr:#x}")
    return 0


def _validate_patched_v3(so: bytes, info: dict) -> None:
    e_phoff = struct.unpack_from("<Q", so, 32)[0]
    e_shoff = struct.unpack_from("<Q", so, 40)[0]
    e_phentsize = struct.unpack_from("<H", so, 54)[0]
    e_phnum = struct.unpack_from("<H", so, 56)[0]
    e_shentsize = struct.unpack_from("<H", so, 58)[0]
    e_shnum = struct.unpack_from("<H", so, 60)[0]
    e_shstrndx = struct.unpack_from("<H", so, 62)[0]
    # PHDR still at original location
    if e_phoff != info["e_phoff_unchanged"]:
        raise RuntimeError("e_phoff was changed unexpectedly")
    if e_phnum != info["e_phnum_unchanged"]:
        raise RuntimeError("e_phnum was changed unexpectedly")
    pt_dynamic_off = None
    pt_dynamic_va = None
    # PT_PHDR covered
    for i in range(e_phnum):
        o = e_phoff + i * e_phentsize
        p_type = struct.unpack_from("<I", so, o)[0]
        p_offset, p_vaddr, _, p_filesz, p_memsz, p_align = struct.unpack_from("<6Q", so, o + 8)
        if p_type == 1 and p_align and (p_vaddr % p_align) != (p_offset % p_align):
            raise RuntimeError(f"LOAD[{i}] alignment mismatch")
        if p_type == 1 and p_offset + p_filesz > len(so):
            raise RuntimeError(f"LOAD[{i}] past EOF")
        if p_type == 2:  # PT_DYNAMIC
            pt_dynamic_off = p_offset
            pt_dynamic_va = p_vaddr
    # Hook branch target
    hook_off = info["hook_file_off"]
    w = struct.unpack_from("<I", so, hook_off)[0]
    imm = w & 0x03FFFFFF
    if imm & (1 << 25):
        imm -= 1 << 26
    target = HOOK_RVA + imm * 4
    if target != info["code_vaddr"]:
        raise RuntimeError(f"hook target {target:#x} != code {info['code_vaddr']:#x}")
    # JNI_OnLoad still present as string in dynstr region (smoke)
    if b"JNI_OnLoad\x00" not in so[:0x20000]:
        print("WARN: JNI_OnLoad string not found in early file (may still be OK)")
    # Real-device bionic: SHT .dynamic offset must equal PT_DYNAMIC p_offset
    if pt_dynamic_off is not None and e_shnum > 0:
        shstr_hdr = e_shoff + e_shstrndx * e_shentsize
        shstr_off = struct.unpack_from("<Q", so, shstr_hdr + 24)[0]
        dyn_sh_off = None
        dyn_sh_addr = None
        for i in range(e_shnum):
            o = e_shoff + i * e_shentsize
            name_off = struct.unpack_from("<I", so, o)[0]
            sh_type = struct.unpack_from("<I", so, o + 4)[0]
            sh_addr = struct.unpack_from("<Q", so, o + 16)[0]
            sh_offset = struct.unpack_from("<Q", so, o + 24)[0]
            nstart = shstr_off + name_off
            end = so.find(b"\x00", nstart)
            name = so[nstart:end].decode("ascii", "replace") if end > nstart else ""
            if name == ".dynamic" or sh_type == 6:  # SHT_DYNAMIC
                dyn_sh_off = sh_offset
                dyn_sh_addr = sh_addr
                break
        if dyn_sh_off is None:
            raise RuntimeError("SHT .dynamic not found")
        if dyn_sh_off != pt_dynamic_off:
            raise RuntimeError(
                f"PT_DYNAMIC/SHT mismatch: p_offset={pt_dynamic_off:#x} "
                f".dynamic.sh_offset={dyn_sh_off:#x} (bionic will reject dlopen)"
            )
        if dyn_sh_addr is not None and pt_dynamic_va is not None and dyn_sh_addr != pt_dynamic_va:
            raise RuntimeError(
                f"PT_DYNAMIC/SHT vaddr mismatch: p_vaddr={pt_dynamic_va:#x} "
                f".dynamic.sh_addr={dyn_sh_addr:#x}"
            )
        print(
            f"  PT_DYNAMIC/.dynamic OK: off={pt_dynamic_off:#x} va={pt_dynamic_va:#x}"
        )
    print("  ELF validation: OK (v3 extend-RX, PHDR unchanged, hook+DYNAMIC OK)")


if __name__ == "__main__":
    sys.exit(main())
