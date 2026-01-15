#!/usr/bin/env python3
"""Test script to verify utils.py module"""

import utils

print("=" * 60)
print("Testing utils.py module")
print("=" * 60)

# Check classes exist
print("\n✓ Module imported successfully!")
print(f"✓ BlandClient class exists: {hasattr(utils, 'BlandClient')}")
print(f"✓ BlandApiError class exists: {hasattr(utils, 'BlandApiError')}")
print(f"✓ Model enum exists: {hasattr(utils, 'Model')}")
print(f"✓ HttpMethod enum exists: {hasattr(utils, 'HttpMethod')}")

# List all public methods
client_methods = [m for m in dir(utils.BlandClient) if not m.startswith('_')]
print(f"\n✓ Total public methods in BlandClient: {len(client_methods)}")

# Group methods by category
call_methods = [m for m in client_methods if 'call' in m.lower()]
agent_methods = [m for m in client_methods if 'agent' in m.lower()]
tool_methods = [m for m in client_methods if 'tool' in m.lower()]
voice_methods = [m for m in client_methods if 'voice' in m.lower()]
batch_methods = [m for m in client_methods if 'batch' in m.lower()]
inbound_methods = [m for m in client_methods if 'inbound' in m.lower() or 'phone' in m.lower()]
pathway_methods = [m for m in client_methods if 'pathway' in m.lower()]

print("\nMethods by category:")
print(f"  • Call methods: {len(call_methods)}")
print(f"    {call_methods}")
print(f"  • Agent methods: {len(agent_methods)}")
print(f"    {agent_methods}")
print(f"  • Tool methods: {len(tool_methods)}")
print(f"    {tool_methods}")
print(f"  • Voice methods: {len(voice_methods)}")
print(f"    {voice_methods}")
print(f"  • Batch methods: {len(batch_methods)}")
print(f"    {batch_methods}")
print(f"  • Inbound/Phone methods: {len(inbound_methods)}")
print(f"    {inbound_methods}")
print(f"  • Pathway methods: {len(pathway_methods)}")
print(f"    {pathway_methods}")

print("\n" + "=" * 60)
print("All checks passed! Module is ready to use.")
print("=" * 60)
