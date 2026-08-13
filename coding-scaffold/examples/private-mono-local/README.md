# Example: local private mono

演示如何对本机私有仓落地策略：

```bash
cd ../../
python3 tools/policy/bootstrap_workspace.py --root examples/private-mono-local --profile local-dev --force
python3 tools/policy/validate_workspace.py --root examples/private-mono-local --policy examples/private-mono-local/.haxitag/workspace-policy.yaml
```
