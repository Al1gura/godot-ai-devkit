# Inventory Serialization

Reference for `skills/inventory-system/SKILL.md` — save/load via Resource → JSON or ConfigFile, with versioning. GDScript + C#.

> ← Back to [SKILL.md](../SKILL.md)

---
## 7. Serialization

Save inventories as `item_id + quantity` pairs. Never serialize the full `ItemData` Resource — instead, look up items at load time from a preloaded registry. This keeps save files small and decoupled from resource paths. Unique mutable items additionally need an `instance_id` and their own state.

Build registries and loaded inventories as candidates, validate them completely, then replace live state once. Reject duplicate catalog IDs. If a saved definition is missing, keep the current inventory and original save unchanged, or preserve an explicit unresolved record for later recovery; never clear the slot and later save that loss.

### GDScript

```gdscript
# item_registry.gd — add as autoload named ItemRegistry
extends Node

# Populate by scanning a folder, or assign manually in _ready().
var _items: Dictionary = {}  # id → ItemData


func _ready() -> void:
    _load_all("res://items/")


func _load_all(folder: String) -> bool:
    var dir := DirAccess.open(folder)
    if dir == null:
        return false
    var candidate: Dictionary = {}
    dir.list_dir_begin()
    var file_name := dir.get_next()
    while file_name != "":
        if file_name.ends_with(".tres"):
            var item: ItemData = load(folder + file_name)
            if item == null or item.id.is_empty():
                push_error("ItemRegistry: invalid item definition '%s'" % file_name)
                return false
            if candidate.has(item.id):
                push_error("ItemRegistry: duplicate item id '%s'" % item.id)
                return false
            candidate[item.id] = item
        file_name = dir.get_next()
    _items = candidate
    return true


func get_item(id: String) -> ItemData:
    return _items.get(id, null)


# ── Serialize ────────────────────────────────────────────────────────────────

func serialize_inventory(inventory: Inventory) -> Array:
    var data: Array = []
    for slot in inventory.slots:
        if slot.is_empty():
            data.append(null)
        else:
            data.append({"id": slot.item.id, "qty": slot.quantity})
    return data


# ── Deserialize ──────────────────────────────────────────────────────────────

func deserialize_inventory(inventory: Inventory, data: Array) -> bool:
    if data.size() > inventory.slots.size():
        push_error("ItemRegistry: saved inventory exceeds capacity")
        return false
    var candidate: Array[InventorySlot] = []
    candidate.resize(inventory.slots.size())
    for i in candidate.size():
        candidate[i] = InventorySlot.new()
    for i in mini(data.size(), inventory.slots.size()):
        var entry: Variant = data[i]
        if entry == null:
            continue
        if not entry is Dictionary:
            push_error("ItemRegistry: invalid inventory entry")
            return false
        var entry_data: Dictionary = entry as Dictionary
        var item_id: String = String(entry_data.get("id", ""))
        var quantity_value: Variant = entry_data.get("qty", null)
        if not (quantity_value is int or quantity_value is float):
            push_error("ItemRegistry: invalid quantity for '%s'" % item_id)
            return false
        var quantity_number: float = float(quantity_value)
        if not is_finite(quantity_number) or quantity_number <= 0.0 or quantity_number != floorf(quantity_number):
            push_error("ItemRegistry: invalid quantity for '%s'" % item_id)
            return false
        var quantity: int = int(quantity_number)
        var item: ItemData = get_item(item_id)
        if item == null or quantity <= 0:
            push_error("ItemRegistry: unresolved or invalid item '%s'" % item_id)
            return false
        var slot := InventorySlot.new()
        slot.item = item
        slot.quantity = quantity
        candidate[i] = slot
    inventory.slots = candidate
    inventory.inventory_changed.emit()
    return true
```

**Usage inside a save system:**

```gdscript
# In SaveManager.save_game():
data["inventory"] = ItemRegistry.serialize_inventory(player.inventory)

# In SaveManager.load_game():
if not ItemRegistry.deserialize_inventory(player.inventory, data["inventory"]):
    push_error("SaveManager: inventory load rejected; live inventory was preserved")
```

### C#

```csharp
// ItemRegistry.cs — add as autoload named ItemRegistry
using System;
using System.Collections.Generic;
using Godot;
using Godot.Collections;

public partial class ItemRegistry : Node
{
    private readonly Dictionary<string, ItemData> _items = new();

    public override void _Ready() => LoadAll("res://items/");

    private bool LoadAll(string folder)
    {
        using var dir = DirAccess.Open(folder);
        if (dir == null) return false;
        var candidate = new Dictionary<string, ItemData>();

        dir.ListDirBegin();
        string fileName = dir.GetNext();
        while (fileName != "")
        {
            if (fileName.EndsWith(".tres"))
            {
                var item = GD.Load<ItemData>(folder + fileName);
                if (item == null || item.Id == "")
                {
                    GD.PushError($"ItemRegistry: invalid item definition '{fileName}'");
                    return false;
                }
                if (!candidate.TryAdd(item.Id, item))
                {
                    GD.PushError($"ItemRegistry: duplicate item id '{item.Id}'");
                    return false;
                }
            }
            fileName = dir.GetNext();
        }
        _items.Clear();
        foreach (var pair in candidate)
            _items.Add(pair.Key, pair.Value);
        return true;
    }

    public ItemData GetItem(string id)
        => _items.TryGetValue(id, out var item) ? item : null;

    // ── Serialize ─────────────────────────────────────────────────────────────

    public Godot.Collections.Array SerializeInventory(Inventory inventory)
    {
        var data = new Godot.Collections.Array();
        foreach (var slot in inventory.Slots)
        {
            if (slot.IsEmpty())
                data.Add(default(Variant));
            else
                data.Add(new Godot.Collections.Dictionary
                {
                    ["id"]  = slot.Item.Id,
                    ["qty"] = slot.Quantity,
                });
        }
        return data;
    }

    // ── Deserialize ───────────────────────────────────────────────────────────

    public bool DeserializeInventory(Inventory inventory, Godot.Collections.Array data)
    {
        if (data.Count > inventory.Slots.Count)
        {
            GD.PushError("ItemRegistry: saved inventory exceeds capacity");
            return false;
        }
        var candidate = new Godot.Collections.Array<InventorySlot>();
        for (int i = 0; i < inventory.Slots.Count; i++)
            candidate.Add(new InventorySlot());
        int count = Mathf.Min(data.Count, inventory.Slots.Count);
        for (int i = 0; i < count; i++)
        {
            if (data[i].VariantType == Variant.Type.Nil)
                continue;

            if (data[i].VariantType != Variant.Type.Dictionary)
            {
                GD.PushError("ItemRegistry: invalid inventory entry");
                return false;
            }

            var entry = data[i].AsGodotDictionary();
            string itemId = entry.ContainsKey("id") ? entry["id"].As<string>() : "";
            if (!entry.ContainsKey("qty"))
            {
                GD.PushError($"ItemRegistry: invalid quantity for '{itemId}'");
                return false;
            }
            Variant quantityValue = entry["qty"];
            if (quantityValue.VariantType != Variant.Type.Int &&
                quantityValue.VariantType != Variant.Type.Float)
            {
                GD.PushError($"ItemRegistry: invalid quantity for '{itemId}'");
                return false;
            }
            double quantityNumber = quantityValue.VariantType == Variant.Type.Int
                ? quantityValue.As<long>()
                : quantityValue.As<double>();
            if (!double.IsFinite(quantityNumber) || quantityNumber <= 0.0 ||
                quantityNumber != Math.Floor(quantityNumber))
            {
                GD.PushError($"ItemRegistry: invalid quantity for '{itemId}'");
                return false;
            }
            int quantity = (int)quantityNumber;
            var item = GetItem(itemId);
            if (item == null || quantity <= 0)
            {
                GD.PushError($"ItemRegistry: unresolved or invalid item '{itemId}'");
                return false;
            }

            candidate[i] = new InventorySlot
            {
                Item     = item,
                Quantity = quantity,
            };
        }
        for (int i = 0; i < candidate.Count; i++)
            inventory.Slots[i] = candidate[i];
        inventory.EmitSignal(Inventory.SignalName.InventoryChanged);
        return true;
    }
}
```

---
