import json
from pathlib import Path
import sqlite3

import pytest

from gallop import mobile_icloud
from gallop.mobile import CloudNotReady, export_mobile

OBJECT = 'B1F70D33-D8B1-4F7C-A387-0C5624A7C9C4'
OLD = 'E23AF157-AFE1-4C42-8E00-FF10C2179BFC'


@pytest.fixture
def bound(tmp_path, monkeypatch):
    target = tmp_path / 'Gallop-Reader'
    target.mkdir()
    dbpath = tmp_path / 'provider.db'
    with sqlite3.connect(dbpath) as db:
        db.executescript('CREATE TABLE server_zones(zonename,documents_etag);'
                         'CREATE TABLE local_items(zone_row_id,item_id,item_parent_id,item_state,item_file_id,item_absolutepath);'
                         'CREATE TABLE server_items(zone_row_id,item_id,item_parent_id,item_state);')
        db.execute('INSERT INTO server_zones VALUES (?,?)', ('iCloud.md.obsidian', 'z'))
        db.execute('INSERT INTO local_items VALUES (1,?,?,0,?,?)',
                   (OBJECT, 'documents', target.stat().st_ino, str(target)))
        db.execute('INSERT INTO server_items VALUES (1,?,?,0)', (OBJECT, 'documents'))
    binding = tmp_path / 'binding.json'
    binding.write_text(json.dumps(dict(target=str(target), database=str(dbpath),
                                      zone='iCloud.md.obsidian', object_id=OBJECT, parent_id='documents')))
    monkeypatch.setattr(mobile_icloud, 'placeholder_identity', lambda p: ({OBJECT}, 0, 1))
    return target, dbpath, binding


def test_stale_placeholder_rejected_even_with_new_server_object(bound, monkeypatch):
    target, dbpath, binding = bound
    before = dbpath.read_bytes()
    monkeypatch.setattr(mobile_icloud, 'placeholder_identity', lambda p: ({OLD}, 0, 1))
    with pytest.raises(ValueError, match='identities disagree'):
        mobile_icloud.validate_target(target, binding)
    assert dbpath.read_bytes() == before


@pytest.mark.parametrize('statement', [
    "UPDATE server_items SET item_parent_id='missing-parent'",
    'DELETE FROM server_items',
    "UPDATE local_items SET item_id='OTHER-OBJECT'",
])
def test_bound_parent_and_object_must_match_live_metadata(bound, statement):
    target, dbpath, binding = bound
    with sqlite3.connect(dbpath) as db:
        db.execute(statement)
    with pytest.raises(ValueError):
        mobile_icloud.validate_target(target, binding)


def test_valid_binding_export_is_recorded_and_cannot_silently_rebind(bound, tmp_path, monkeypatch):
    from gallop import mobile
    target, dbpath, binding = bound
    source = tmp_path / 'Main'
    (source / '.obsidian').mkdir(parents=True)
    state = tmp_path / 'state'
    monkeypatch.setattr(mobile, 'wait_cloud_directory', lambda p: None)
    result = export_mobile(source, target, state, icloud_binding=binding)
    assert result['written'] == 2
    receipt = (state / 'receipt.json').read_bytes()
    assert json.loads(receipt)['icloud_target']['object_id'] == OBJECT
    with pytest.raises(CloudNotReady, match='explicit rebind'):
        export_mobile(source, target, state)
    assert (state / 'receipt.json').read_bytes() == receipt


def test_stale_binding_stops_before_any_export_mutation(bound, tmp_path, monkeypatch):
    target, dbpath, binding = bound
    source = tmp_path / 'Main'
    (source / '.obsidian').mkdir(parents=True)
    old = target / 'Today.md'
    old.write_bytes(b'Old mirror retained')
    old_id = old.stat().st_ino
    state = tmp_path / 'state'
    monkeypatch.setattr(mobile_icloud, 'placeholder_identity', lambda p: ({OLD}, 0, 1))
    with pytest.raises(CloudNotReady, match='identities disagree'):
        export_mobile(source, target, state, icloud_binding=binding, refresh=True)
    assert old.read_bytes() == b'Old mirror retained'
    assert old.stat().st_ino == old_id
    assert not state.exists()
