#!/usr/bin/env python3
"""
Simplified inventory merge payload (ARM64).

Strategy proven on device (Houdini):
  - open/read inventory_extra.json
  - scan for "digits":digits pairs (Cards keys)
  - AddCardToInventory(id, cards, count, MethodInfo=NULL)
    (first insert when missing sets absolute count; game itself uses MethodInfo=null)

Skips GetCardInventoryCount (that path was crashing in the complex parser).
Uses max-ish behavior: AddCard only when count > 0; for already-owned cards may
over-add on repeated SetLocal — acceptable for local offline testing. For stricter
max, a follow-up can reintroduce GetCount once register hygiene is proven.
"""

from __future__ import annotations

from keystone import KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN, Ks

ADD_CARD = 0x1FEB97C
ORIG_TAIL = 0x180423C
OPEN = 0x03780710
READ = 0x037806C0
CLOSE = 0x03780720
MALLOC = 0x037805F0
FREE = 0x03780600

PATH = (
    b"/storage/emulated/0/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json\x00"
)


def _load(reg: str, va: int) -> str:
    page = va & ~0xFFF
    off = va & 0xFFF
    return f"    adrp {reg}, {page:#x}\n    add {reg}, {reg}, #{off:#x}\n"


def build(code_va: int, path_va: int) -> bytes:
    asm = f"""
hook:
    sub sp, sp, #0x60
    stp x19, x20, [sp]
    stp x21, x30, [sp, #0x10]
    stp x22, x23, [sp, #0x20]
    stp x24, x25, [sp, #0x30]
    stp x26, x27, [sp, #0x40]
    // x19=inventory on entry
    cbz x19, done
    ldr x20, [x19, #0x10]
    cbz x20, done
    ldr x8, [x20]
    cbz x8, done
{_load("x0", path_va)}
    mov x1, xzr
    bl {OPEN:#x}
    cmp w0, #0
    b.lt done
    mov w21, w0
    mov x0, #0x10000
    bl {MALLOC:#x}
    cbz x0, close_only
    mov x22, x0
    mov w0, w21
    mov x1, x22
    mov x2, #0xFF00
    bl {READ:#x}
    mov x23, x0
    mov w0, w21
    bl {CLOSE:#x}
    cmp x23, #1
    b.lt freemem
    mov w8, #0
    strb w8, [x22, x23]
    mov x24, x22
    add x25, x22, x23
scan:
    cmp x24, x25
    b.hs freemem
    ldrb w8, [x24]
    add x24, x24, #1
    cmp w8, #0x22
    b.ne scan
    // parse key digits
    mov x26, x24
    mov w0, #0
    mov w1, #0
kdig:
    cmp x26, x25
    b.hs scan
    ldrb w8, [x26]
    cmp w8, #0x22
    b.eq kend
    cmp w8, #0x30
    b.lt scan
    cmp w8, #0x39
    b.gt scan
    mov w9, #10
    mul w0, w0, w9
    sub w8, w8, #0x30
    add w0, w0, w8
    add w1, w1, #1
    add x26, x26, #1
    cmp w1, #9
    b.lt kdig
    b scan
kend:
    cbz w1, advance_after_key
    mov w27, w0
    add x26, x26, #1
sk_ws1:
    cmp x26, x25
    b.hs freemem
    ldrb w8, [x26]
    cmp w8, #0x20
    b.eq sk_ws1a
    cmp w8, #0x09
    b.eq sk_ws1a
    cmp w8, #0x0a
    b.eq sk_ws1a
    cmp w8, #0x0d
    b.eq sk_ws1a
    b after_ws1
sk_ws1a:
    add x26, x26, #1
    b sk_ws1
after_ws1:
    ldrb w8, [x26]
    cmp w8, #0x3a
    b.ne advance_cursor
    add x26, x26, #1
sk_ws2:
    cmp x26, x25
    b.hs freemem
    ldrb w8, [x26]
    cmp w8, #0x20
    b.eq sk_ws2a
    cmp w8, #0x09
    b.eq sk_ws2a
    b vparse
sk_ws2a:
    add x26, x26, #1
    b sk_ws2
vparse:
    mov w0, #0
    mov w1, #0
vdig:
    cmp x26, x25
    b.hs vdone
    ldrb w8, [x26]
    cmp w8, #0x30
    b.lt vdone
    cmp w8, #0x39
    b.gt vdone
    mov w9, #10
    mul w0, w0, w9
    sub w8, w8, #0x30
    add w0, w0, w8
    add w1, w1, #1
    add x26, x26, #1
    b vdig
vdone:
    cbz w1, advance_cursor
    cbz w0, advance_cursor
    // skip id 0 (e.g. bad parse)
    cbz w27, advance_cursor
    // AddCard(id, dict, count, MethodInfo=NULL)
    mov w2, w0
    mov w0, w27
    mov x1, x20
    mov x3, xzr
    bl {ADD_CARD:#x}
advance_cursor:
    mov x24, x26
    b scan
advance_after_key:
    mov x24, x26
    b scan
freemem:
    mov x0, x22
    bl {FREE:#x}
    b done
close_only:
    mov w0, w21
    bl {CLOSE:#x}
done:
    ldp x19, x20, [sp]
    mov x0, x20
    mov x1, x19
    ldp x21, x30, [sp, #0x10]
    ldp x22, x23, [sp, #0x20]
    ldp x24, x25, [sp, #0x30]
    ldp x26, x27, [sp, #0x40]
    add sp, sp, #0x60
    ldp x20, x19, [sp, #0x10]
    ldp x30, x21, [sp], #0x20
    b {ORIG_TAIL:#x}
"""
    ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    enc, _ = ks.asm(asm, code_va)
    return bytes(enc)


def build_full(code_va: int) -> tuple[bytes, int]:
    """Return (payload_bytes, path_va)."""
    # two-pass for path placement
    path_va = code_va + 0x400
    code = build(code_va, path_va)
    code_size = (len(code) + 15) & ~15
    path_va = code_va + code_size
    code = build(code_va, path_va)
    code_size = (len(code) + 15) & ~15
    path_va = code_va + code_size
    code = build(code_va, path_va)
    code_size = (len(code) + 15) & ~15
    payload = bytearray(code)
    if len(payload) < code_size:
        payload.extend(b"\x00" * (code_size - len(payload)))
    payload.extend(PATH)
    return bytes(payload), path_va
