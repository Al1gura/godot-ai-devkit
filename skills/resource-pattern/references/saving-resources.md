# Saving Custom Resources

Reference for `skills/resource-pattern/SKILL.md` — `ResourceSaver.save()` for persistent state. GDScript + C#.

> ← Back to [SKILL.md](../SKILL.md)

---
## 9. Saving Custom Resources

Use `ResourceSaver` to write trusted Resources to disk at runtime (for example, procedurally generated developer-controlled content). For user saves, removable catalogs, or mod data that needs explicit validation, migration, and recovery, prefer a declared data format such as JSON or ConfigFile.

### GDScript

```gdscript
func save_resource(res: Resource, path: String) -> bool:
    var err := ResourceSaver.save(res, path)
    if err != OK:
        push_error("Failed to save resource to '%s' — error %d" % [path, err])
        return false
    return true


# .tres — human-readable text, good for debugging and version control
save_resource(my_item, "user://generated/custom_sword.tres")

# .res — binary, smaller and faster to load, use in production builds
save_resource(my_item, "user://generated/custom_sword.res")
```

### C#

```csharp
public bool SaveResource(Resource res, string path)
{
    var err = ResourceSaver.Save(res, path);
    if (err != Error.Ok)
    {
        GD.PushError($"Failed to save resource to '{path}' — error {err}");
        return false;
    }
    return true;
}

// .tres — human-readable, for debugging and version control
SaveResource(myItem, "user://generated/custom_sword.tres");

// .res — binary, faster to load, use in production
SaveResource(myItem, "user://generated/custom_sword.res");
```

**Format guidance:**

| Format | Pros | Cons | Use When |
|---|---|---|---|
| `.tres` | Human-readable, diffable, debuggable | Larger file, slower to parse | Development, version control, trusted editor-authored data |
| `.res` | Compact binary, faster to load | Not human-readable | Production builds, shipped game data |

> **Security:** Treat `.tres` and `.res` as trusted Godot resource formats, not plain data. Loading them may resolve scripted classes and related resources. Never load them directly from untrusted uploads or downloaded mods; use a declared and validated data format for untrusted content.

For irreplaceable data, do not save directly over the only valid file. Write a temporary file, close and re-read it, validate the decoded resource, then replace the target with a risk-appropriate backup and recovery path.

---
