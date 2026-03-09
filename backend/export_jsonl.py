import json
from backend.database import SessionLocal
from backend.models import AutomationTemplateModel

def export_jsonl():
    db = SessionLocal()
    try:
        templates = db.query(AutomationTemplateModel).all()

        with open("deepseek_training_data.jsonl", "w") as f:
            for template in templates:
                # Prepare data for formatting
                trigger_app = template.trigger_app
                action_apps = template.action_apps
                complexity_score = template.complexity_score
                monthly_opex = template.monthly_opex
                maintenance_level = template.maintenance_level

                # Construct ChatML message
                message = {
                    "messages": [
                        {"role": "system", "content": "You are an expert Automation Architect."},
                        {
                            "role": "user",
                            "content": f"Design an automation connecting {trigger_app} and {action_apps}. What is the cost and complexity?"
                        },
                        {
                            "role": "assistant",
                            "content": f"<think>The user is asking for an integration between {trigger_app} and {action_apps}. I need to evaluate the graph metrics. The calculated complexity is {complexity_score}/5 and the monthly OPEX is ${monthly_opex}.</think> To connect these systems, you should use {trigger_app} as your trigger, followed by {action_apps} as your actions. This is a {maintenance_level} maintenance setup with a complexity score of {complexity_score}/5. The estimated monthly operational cost is ${monthly_opex}."
                        }
                    ]
                }

                f.write(json.dumps(message) + "\n")

        print(f"Exported {len(templates)} templates to deepseek_training_data.jsonl.")

    finally:
        db.close()

if __name__ == "__main__":
    export_jsonl()
