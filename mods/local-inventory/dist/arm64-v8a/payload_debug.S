
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
    b 0x180423c

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

    adrp x0, 0x4004000
    add x0, x0, #0x0

    bl try_open

    cbnz w0, got_fd

    adrp x0, 0x4004000
    add x0, x0, #0x5c

    bl try_open

    cbnz w0, got_fd

    adrp x0, 0x4004000
    add x0, x0, #0xac

    bl try_open

    cbnz w0, got_fd


    b merge_epilogue
got_fd:
    mov w22, w0
    mov x0, #262160
    bl 0x37805f0
    cbz x0, close_fail
    mov x25, x0
    mov x23, x0
    mov w0, w22
    mov x1, x23
    mov x2, #262144
    bl 0x37806c0
    mov x24, x0
    mov w0, w22
    bl 0x3780720
    mov w22, wzr
    cmp x24, #0
    b.le merge_epilogue
    mov w8, #0
    strb w8, [x23, x24]
    mov x0, x23
    bl strip_bom
    mov x23, x0

    adrp x1, 0x4004000
    add x1, x1, #0xf0


    mov x0, x23
    bl find_key_value
    cbz x0, merge_epilogue
    mov x1, xzr
    mov x2, #10
    bl 0x3781110
    cmp x0, #1
    b.ne merge_epilogue
    cbz x20, do_heroes

    adrp x1, 0x4004000
    add x1, x1, #0x100


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

    adrp x1, 0x4004000
    add x1, x1, #0x108


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
    bl 0x3780720
merge_epilogue:
    mov x0, x25
    cbz x0, merge_restore
    bl 0x3780600
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
    bl 0x3780710
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
    bl 0x37807c0
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
    bl 0x3780f50
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
    stp x29, x30, [sp, #-0x60]!
    stp x19, x20, [sp, #0x10]
    stp x21, x22, [sp, #0x20]
    stp x23, x24, [sp, #0x30]
    stp x25, x26, [sp, #0x40]
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
    cmp w0, #0
    b.lt pom_done
    mov w25, w0
    mov x19, x1
    cbnz w21, pom_hero
    mov x0, x22
    mov x1, x24
    bl parse_digits_key
    cmp w0, #0
    b.lt pom_loop
    mov w26, w0
    cbz x20, pom_loop
    mov w0, w26
    mov x1, x20
    bl 0x1febb60
    mov w27, w0
    cmp w25, w27
    b.le pom_loop
    sub w2, w25, w27
    mov w0, w26
    mov x1, x20
    bl 0x1feb97c
    b pom_loop
pom_hero:
    cbz x20, pom_loop
    sub sp, sp, #0x80
    mov x0, sp
    mov x1, x22
    mov x2, x24
    bl 0x3780210
    mov w8, #0
    mov x9, sp
    strb w8, [x9, x24]
    mov x0, sp
    bl 0x178cc3c
    add sp, sp, #0x80
    cbz x0, pom_loop
    mov x26, x0
    mov x0, x26
    mov x1, x20
    bl 0x1febbf0
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
    ldp x29, x30, [sp], #0x60
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
    adrp x8, 0x3c70000
    add x8, x8, #0x897
    ldrb w9, [x8]
    tbnz w9, #0, hds_inited
    adrp x0, 0x3941000
    add x0, x0, #0xd8
    ldr x0, [x0]
    bl 0x1804290
    adrp x8, 0x3c70000
    add x8, x8, #0x897
    mov w9, #1
    strb w9, [x8]
hds_inited:
    adrp x8, 0x3941000
    add x8, x8, #0xd8
    ldr x8, [x8]
    cbz x8, hds_done
    ldr x3, [x8]
    cbz x3, hds_done
    mov x0, x19
    mov x1, x20
    mov w2, w21
    bl 0x265b1fc
hds_done:
    ldr x21, [sp, #0x20]
    ldp x19, x20, [sp, #0x10]
    ldp x29, x30, [sp], #0x30
    ret
