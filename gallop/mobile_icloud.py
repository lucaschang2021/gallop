"""Fail-closed identity check for an explicitly bound iCloud reading vault.

The Apple metadata DB is opened read-only. No provider state is repaired here.
Opaque Cloud Files identities are only inspected for Apple's object UUID;
an unrecognized format stops export instead of falling back to pathname.
"""
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import re
import sqlite3


def placeholder_identity(path: Path) -> tuple[set[str], int, int]:
    if os.name != 'nt':
        raise ValueError('iCloud object validation requires Windows')
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, c.c_void_p,
                                   w.DWORD, w.DWORD, w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]
    api = c.WinDLL('cldapi')
    api.CfGetPlaceholderInfo.argtypes = [w.HANDLE, c.c_int, c.c_void_p,
                                        w.DWORD, c.POINTER(w.DWORD)]
    api.CfGetPlaceholderInfo.restype = c.c_long
    handle = kernel.CreateFileW(str(path), 0x80, 7, None, 3, 0x02000000, None)
    if handle == c.c_void_p(-1).value:
        raise OSError(c.get_last_error(), 'Cannot read iCloud placeholder identity')
    try:
        buffer = c.create_string_buffer(65536)
        returned = w.DWORD()
        hr = api.CfGetPlaceholderInfo(handle, 0, buffer, len(buffer), c.byref(returned))
        if hr != 0 or returned.value < 28:
            raise ValueError('iCloud placeholder identity is unavailable')
        size = c.c_uint32.from_buffer(buffer, 24).value
        if size > returned.value - 28:
            raise ValueError('Invalid iCloud placeholder identity length')
        raw = buffer.raw[28:28 + size]
        ids = {s.decode('ascii').upper() for s in re.findall(
            rb'[A-Fa-f0-9]{8}(?:-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12}', raw)}
        return ids, c.c_uint32.from_buffer(buffer, 0).value, c.c_uint32.from_buffer(buffer, 4).value
    finally:
        kernel.CloseHandle(handle)


def validate_target(target: Path, binding_file: Path) -> dict:
    binding = json.loads(binding_file.read_text(encoding='utf-8'))
    if (Path(binding['target']).resolve() != target.resolve()
            or binding['zone'] != 'iCloud.md.obsidian'
            or binding['parent_id'] != 'documents'):
        raise ValueError('Binding is not for this Obsidian iCloud vault')
    expected = binding['object_id'].upper()
    db = sqlite3.connect(Path(binding['database']).resolve().as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        zone = db.execute('SELECT rowid,documents_etag FROM server_zones WHERE zonename=?',
                          (binding['zone'],)).fetchall()
        if len(zone) != 1 or not zone[0][1]:
            raise ValueError('Obsidian iCloud documents container is not acknowledged')
        local = db.execute('SELECT item_id,item_parent_id,item_state,item_file_id FROM local_items '
                           'WHERE zone_row_id=? AND item_absolutepath=?',
                           (zone[0][0], str(target))).fetchall()
        wanted = (expected, binding['parent_id'], 0, target.stat().st_ino)
        if local != [wanted]:
            raise ValueError('Local iCloud metadata does not match the bound object/parent')
        remote = db.execute('SELECT item_parent_id,item_state FROM server_items '
                            'WHERE zone_row_id=? AND item_id=?', (zone[0][0], expected)).fetchall()
        if remote != [(binding['parent_id'], 0)]:
            raise ValueError('Bound iCloud object/parent is absent from server metadata')
        ids, pin, in_sync = placeholder_identity(target)
        if ids != {expected}:
            raise ValueError('Stale iCloud target: Windows placeholder and server object identities disagree')
        if pin == 3 or in_sync != 1:
            raise ValueError('Bound iCloud target is excluded or not acknowledged')
    finally:
        db.close()
    return {key: binding[key] for key in ('zone', 'object_id', 'parent_id')}
