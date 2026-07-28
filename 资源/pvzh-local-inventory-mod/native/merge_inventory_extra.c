/*
 * Reference implementation: merge inventory_extra.json into PlayerInventory.
 *
 * This C file documents the intended runtime behavior. The production payload
 * is assembled by scripts/build_and_patch.py (Keystone ARM64) and injected into
 * libil2cpp.so as a new PT_LOAD segment. Keep this file in sync when changing
 * merge semantics.
 *
 * Hook: after PlayerInventoryHolderImpl.SetLocalPlayerInventory stores the
 * inventory pointer, call merge_inventory_extra(inventory).
 *
 * Constraints:
 *  - libc only (+ il2cpp exports already in the SO)
 *  - silent failure on any error
 *  - never touch PlayerInventoryDelta
 *  - Cards/Heroes: max(existing, extra)
 */

#include <stdint.h>
#include <stddef.h>

/* --- layout from dump.cs --- */
#define OFF_CARDS  0x10
#define OFF_HEROES 0x18

/* Game RVAs (this snapshot) — resolved as absolute VA inside libil2cpp.so */
/* PlayerInventoryUtility.GetCardInventoryCount  RVA 0x1FEBB60 */
/* PlayerInventoryUtility.AddCardToInventory     RVA 0x1FEB97C */
/* PlayerInventoryUtility.GetHeroInventoryCount  RVA 0x1FEBBF0 */
/* il2cpp_string_new                            VA  0x0178CC3C */

#define SCHEMA_VERSION_SUPPORTED 1
#define MAX_FILE_BYTES (256 * 1024)

/* Candidate paths (Unity Android files root variants) */
static const char *const k_paths[] = {
    "/storage/emulated/0/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json",
    "/sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json",
    "/data/data/com.ea.gp.pvzheroes/files/cache/mod/inventory_extra.json",
    NULL
};

/* Typedefs matching IL2CPP AArch64 calling convention */
typedef int  (*fn_get_card_count)(int card_id, void *cards_dict);
typedef void (*fn_add_card)(int card_id, void *cards_dict, int quantity);
typedef int  (*fn_get_hero_count)(void *hero_str, void *heroes_dict);
typedef void *(*fn_il2cpp_string_new)(const char *utf8);

/* Implemented by the injected payload (addresses fixed at patch time). */
extern fn_get_card_count     g_GetCardInventoryCount;
extern fn_add_card           g_AddCardToInventory;
extern fn_get_hero_count     g_GetHeroInventoryCount;
extern fn_il2cpp_string_new  g_il2cpp_string_new;

/* Forward: set Dictionary<string,int>[key]=value via game MethodInfo path */
extern void heroes_set_item(void *heroes_dict, void *managed_str, int value);

static int is_ws(char c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r';
}

static char *skip_ws(char *p) {
    while (p && *p && is_ws(*p)) p++;
    return p;
}

/* Find "key" then ':' and return pointer to value start, or NULL. */
static char *find_json_key_value(char *buf, const char *key) {
    /* naive search; adequate for small controlled mod files */
    char pattern[96];
    /* pattern built as "key" — caller passes key without quotes */
    size_t klen = 0;
    while (key[klen]) klen++;
    if (klen + 3 >= sizeof(pattern)) return NULL;
    pattern[0] = '"';
    for (size_t i = 0; i < klen; i++) pattern[i + 1] = key[i];
    pattern[klen + 1] = '"';
    pattern[klen + 2] = 0;

    char *p = buf;
    for (;;) {
        char *hit = p;
        /* strstr-like */
        while (*hit) {
            size_t i = 0;
            while (pattern[i] && hit[i] == pattern[i]) i++;
            if (!pattern[i]) break;
            hit++;
        }
        if (!*hit) return NULL;
        p = hit + klen + 2;
        p = skip_ws(p);
        if (*p != ':') {
            /* continue search after this hit */
            continue;
        }
        p++;
        return skip_ws(p);
    }
}

static long parse_nonneg_int(char **pp) {
    char *p = skip_ws(*pp);
    if (*p < '0' || *p > '9') {
        *pp = p;
        return -1;
    }
    long v = 0;
    while (*p >= '0' && *p <= '9') {
        v = v * 10 + (*p - '0');
        if (v > 0x7fffffffL) {
            *pp = p;
            return -1;
        }
        p++;
    }
    *pp = p;
    return v;
}

static void merge_one_card(void *cards, int card_id, int extra) {
    if (!cards || extra < 0) return;
    int existing = g_GetCardInventoryCount(card_id, cards);
    if (extra > existing) {
        g_AddCardToInventory(card_id, cards, extra - existing);
    }
}

static void merge_one_hero(void *heroes, const char *hero_id, int extra) {
    if (!heroes || !hero_id || extra < 0) return;
    void *s = g_il2cpp_string_new(hero_id);
    if (!s) return;
    int existing = g_GetHeroInventoryCount(s, heroes);
    if (extra > existing) {
        heroes_set_item(heroes, s, extra);
    }
}

/* Parse object body starting at '{', call merge for each pair.
 * kind: 0=Cards (int keys), 1=Heroes (string keys). */
static void parse_object_merge(char *brace, void *dict, int kind) {
    if (!brace || *brace != '{' || !dict) return;
    char *p = brace + 1;
    for (;;) {
        p = skip_ws(p);
        if (*p == '}') return;
        if (*p == ',') { p++; continue; }
        if (*p != '"') return; /* malformed → silent stop this object */
        p++;
        char keybuf[128];
        size_t ki = 0;
        while (*p && *p != '"') {
            if (ki + 1 < sizeof(keybuf)) keybuf[ki++] = *p;
            p++;
        }
        if (*p != '"') return;
        p++;
        keybuf[ki] = 0;
        p = skip_ws(p);
        if (*p != ':') return;
        p++;
        long val = parse_nonneg_int(&p);
        if (val < 0) return;
        if (kind == 0) {
            /* Cards: key must be decimal digits */
            int ok = 1, id = 0;
            if (!keybuf[0]) ok = 0;
            for (size_t i = 0; keybuf[i]; i++) {
                if (keybuf[i] < '0' || keybuf[i] > '9') { ok = 0; break; }
                id = id * 10 + (keybuf[i] - '0');
            }
            if (ok) merge_one_card(dict, id, (int)val);
        } else {
            merge_one_hero(dict, keybuf, (int)val);
        }
        p = skip_ws(p);
        if (*p == ',') { p++; continue; }
        if (*p == '}') return;
        /* tolerate trailing junk by stopping */
        return;
    }
}

/* Public entry: x0 = PlayerInventory* (managed object) */
void merge_inventory_extra(void *inventory) {
    if (!inventory) return;

    void *cards  = *(void **)((char *)inventory + OFF_CARDS);
    void *heroes = *(void **)((char *)inventory + OFF_HEROES);

    /* open first existing path */
    int fd = -1;
    for (int i = 0; k_paths[i]; i++) {
        /* access(path, R_OK) then open — payload uses open(O_RDONLY) */
        /* if success break */
        (void)k_paths[i];
    }
    if (fd < 0) return;

    /* read up to MAX_FILE_BYTES, parse schemaVersion==1, merge Cards/Heroes */
    (void)cards;
    (void)heroes;
    /* full body lives in the assembled payload */
}
