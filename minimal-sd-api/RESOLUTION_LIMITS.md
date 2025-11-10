# Resolution Limits - RX 6700 XT + ROCm 6.4

## Testing Summary (November 10, 2025)

### Stable Resolutions ✅
- **768×768** - Always works (589,824 pixels)
- **768×832** - Works (638,976 pixels)
- **832×832** - Works reliably (692,224 pixels)

### Unstable/Crash Resolutions ❌
- **832×768** - CRASHES with `malloc(): invalid size (unsorted)` ⚠️
- **864×864** - UNSTABLE (works sometimes, crashes other times)
- **880×880** - CRASHES with `munmap_chunk(): invalid pointer`
- **1024×1024** - CRASHES with `munmap_chunk(): invalid pointer`

## Key Findings

### 1. Asymmetric Behavior
**Width vs Height matters!**
- ✅ 768×832 (wide) works
- ❌ 832×768 (tall) crashes with DIFFERENT error

This suggests the crash is not purely about total pixel count or individual dimension limits.

### 2. Multiple Error Types
Different resolutions trigger different memory errors:
- **`malloc(): invalid size (unsorted)`** - 832×768
- **`munmap_chunk(): invalid pointer`** - 880×880, 1024×1024

### 3. Unstable Edge Cases
- 864×864 sometimes works, sometimes crashes
- Indicates we're at the absolute edge of what's possible

## Recommended Limits for Production

### Conservative (Recommended)
```python
MAX_WIDTH = 768
MAX_HEIGHT = 832  # or 768 for symmetric safety
```

### Aggressive (May be unstable)
```python
MAX_WIDTH = 832
MAX_HEIGHT = 832
# Warning: May have occasional failures
```

## Validation Strategy

For the API, implement:

```python
def validate_resolution(width, height):
    # Must be divisible by 8
    if width % 8 != 0 or height % 8 != 0:
        return False, "Dimensions must be divisible by 8"
    
    # Safe conservative limits
    if width > 768 or height > 832:
        return False, f"Maximum: 768×832 (requested: {width}×{height})"
    
    # Minimum practical size
    if width < 64 or height < 64:
        return False, "Minimum: 64×64"
    
    return True, "OK"
```

## Testing Notes

- Phase 1 optimizations enabled (attention slicing, VAE tiling, etc.)
- ROCm 6.4.0 (host) + 6.4.4 (container)
- AMD RX 6700 XT (12GB VRAM, 40 CUs)
- PyTorch 2.7.1
- Model: CompVis/stable-diffusion-v1-4

## Next Steps

1. ✅ Implement resolution validation in API
2. Test if 768×896, 768×960, 768×1024 work (pushing height further)
3. Investigate why width/height are asymmetric
4. Consider if model CPU offload settings affect limits
