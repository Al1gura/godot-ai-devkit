# Version Migration

Reference for `skills/save-load/SKILL.md` — incremental migration from older save versions on load.

> ← Back to [SKILL.md](../SKILL.md)

---
## 6. Version Migration

Always store a `version` integer in every save file. Apply migrations incrementally so any old save can be brought forward to the current format regardless of how many versions it has missed.

The snippets below illustrate field transformations only. A production loader must first deep-copy the source, reject `version > CURRENT_VERSION` without changing it, run exactly one `vN → vN+1` transformation at a time, validate each candidate, and replace or write the authoritative state only after the full chain succeeds.

```gdscript
func _migrate(data: Dictionary) -> Dictionary:
	var version: int = data.get("version", 0)

	if version < 1:
		# v0 → v1: inventory did not exist, add empty array
		data["player"]["inventory"] = []
		version = 1

	if version < 2:
		# v1 → v2: skills system added, seed from empty array
		data["player"]["skills"] = []
		version = 2

	# v2 → v3: add stamina stat with default value
	if version < 3:
		data["player"]["stamina"] = 100
		version = 3

	data["version"] = CURRENT_VERSION
	return data
```

```csharp
using Godot;
using Godot.Collections;

public partial class SaveMigrator : Node
{
    private const int CurrentVersion = 3;

    public Dictionary Migrate(Dictionary data)
    {
        int version = data.ContainsKey("version") ? (int)data["version"] : 0;

        if (version < 1)
        {
            // v0 → v1: inventory did not exist, add empty array
            if (!data.ContainsKey("player"))
                data["player"] = new Dictionary();
            ((Dictionary)data["player"])["inventory"] = new Array();
            version = 1;
        }

        if (version < 2)
        {
            // v1 → v2: skills system added, seed from empty array
            if (!data.ContainsKey("player"))
                data["player"] = new Dictionary();
            ((Dictionary)data["player"])["skills"] = new Array();
            version = 2;
        }

        if (version < 3)
        {
            // v2 → v3: add stamina stat with default value
            if (!data.ContainsKey("player"))
                data["player"] = new Dictionary();
            ((Dictionary)data["player"])["stamina"] = 100;
            version = 3;
        }

        data["version"] = CurrentVersion;
        return data;
    }
}
```

Key rules:
- Give each independently stored format a discriminator plus an integer schema version; changing field meaning requires a version bump
- Migrate a deep copy step by step and validate after every step; failure preserves the original bytes and current live state
- Reject future versions without rewriting, downgrading, or treating them as empty data
- Make repeat loading stable: an already migrated record must not create duplicates, charge costs again, or receive new IDs
- Preserve unknown or unavailable user state when possible; never infer identity from display names, paths, or array positions
- Use `data.get("key", default)` only where the migration contract defines that default; do not use defaults to hide corruption

---
