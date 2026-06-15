# Quick Modes Reference Card

## 🎯 Three Modes at a Glance

```bash
# 1️⃣ DRY-RUN - Test processing only (no calendar needed)
python calhero.py --dry-run

# 2️⃣ CHECK-ONLY - Check duplicates (read-only, requires calendar)
python calhero.py --check-only

# 3️⃣ NORMAL - Full operation (creates events)
python calhero.py
```

---

## 📊 Quick Comparison

| Mode | Calendar Needed? | What It Does |
|------|-----------------|--------------|
| `--dry-run` | ❌ No | Test image processing |
| `--check-only` | ✅ Yes | Check duplicates (no create) |
| Normal | ✅ Yes | Create events |

---

## 💡 Common Scenarios

**"I want to test OCR without calendar"**
```bash
python calhero_ml.py --dry-run --debug
```

**"I want to see what would be created"**
```bash
python calhero.py --check-only
```

**"I want to create events"**
```bash
python calhero.py
```

**"Test with my test calendar first"**
```bash
python calhero.py --check-only --calendar-id "${TEST_CALENDAR_ID}"
python calhero.py --calendar-id "${TEST_CALENDAR_ID}"
```

---

## 🚫 Invalid Combinations

```bash
# ❌ Cannot use together
python calhero.py --dry-run --check-only
```

---

## 📚 Full Docs

- **MODES_USAGE_GUIDE.md** - Complete guide with examples
- **MODES_IMPLEMENTATION_SUMMARY.md** - Technical details
- **ENV_CONFIGURATION_GUIDE.md** - Setup instructions
