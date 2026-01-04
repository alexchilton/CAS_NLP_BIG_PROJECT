from dnd_rag_system.systems.action_validator import ActionValidator, ActionType

# Test steal detection
validator = ActionValidator(debug=True)

test_inputs = [
    "steal the healing potion",
    "swipe the healing potion", 
    "pocket the potion",
    "use the healing potion",
]

for inp in test_inputs:
    intent = validator.analyze_intent(inp)
    print(f"Input: '{inp}'")
    print(f"  Action Type: {intent.action_type}")
    print(f"  Resource: {intent.resource}")
    print()
