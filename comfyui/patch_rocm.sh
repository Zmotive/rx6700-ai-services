#!/bin/bash
# Patch ComfyUI for ROCm compatibility

echo "🔧 Applying ROCm compatibility patch to ComfyUI..."

PATCH_FILE="/workspace/ComfyUI/comfy/model_management.py"

if [ -f "$PATCH_FILE" ]; then
    # Backup original
    cp "$PATCH_FILE" "$PATCH_FILE.bak" 2>/dev/null || true
    
    # Check how many locations need patching
    patch_count=$(grep -c "# ROCm fallback" "$PATCH_FILE" 2>/dev/null || echo "0")
    
    if [ "$patch_count" -eq "2" ]; then
        echo "✅ Already fully patched, skipping..."
        exit 0
    fi
    
    # Patch the get_total_memory and get_free_memory functions to handle ROCm
    python3 << 'EOF'
with open("/workspace/ComfyUI/comfy/model_management.py", "r") as f:
    lines = f.readlines()

# Find and replace both mem_get_info calls
patches_applied = 0
i = 0
while i < len(lines):
    line = lines[i]
    
    # First occurrence: get_total_memory (line ~223)
    if '_, mem_total_cuda = torch.cuda.mem_get_info(dev)' in line and patches_applied == 0:
        indent = ' ' * 12
        lines[i] = f"{indent}try:\n"
        lines.insert(i+1, f"{indent}    _, mem_total_cuda = torch.cuda.mem_get_info(dev)\n")
        lines.insert(i+2, f"{indent}except RuntimeError:\n")
        lines.insert(i+3, f"{indent}    # ROCm fallback: use device properties\n")
        lines.insert(i+4, f"{indent}    props = torch.cuda.get_device_properties(dev)\n")
        lines.insert(i+5, f"{indent}    mem_total_cuda = props.total_memory\n")
        patches_applied += 1
        i += 6  # Skip the inserted lines
        continue
    
    # Second occurrence: get_free_memory (line ~1271)
    if 'mem_free_cuda, _ = torch.cuda.mem_get_info(dev)' in line and patches_applied == 1:
        indent = ' ' * 12
        lines[i] = f"{indent}try:\n"
        lines.insert(i+1, f"{indent}    mem_free_cuda, _ = torch.cuda.mem_get_info(dev)\n")
        lines.insert(i+2, f"{indent}except RuntimeError:\n")
        lines.insert(i+3, f"{indent}    # ROCm fallback: estimate free memory\n")
        lines.insert(i+4, f"{indent}    props = torch.cuda.get_device_properties(dev)\n")
        lines.insert(i+5, f"{indent}    mem_free_cuda = props.total_memory - torch.cuda.memory_allocated(dev)\n")
        patches_applied += 2
        i += 6
        continue
    
    i += 1

with open("/workspace/ComfyUI/comfy/model_management.py", "w") as f:
    f.writelines(lines)

print(f"✅ Patch applied successfully ({patches_applied} locations)")
EOF
    
    echo "✅ ComfyUI patched for ROCm compatibility"
else
    echo "⚠️  Patch file not found, skipping..."
fi
