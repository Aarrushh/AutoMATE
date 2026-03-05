import sqlite3
import json
import os

# Use the database in the same directory as the script
DB_PATH = os.path.join(os.path.dirname(__file__), "automations.db")
OUTPUT_FILE = "deepseek_training_data.jsonl"

def export_to_jsonl():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Connect to the database and retrieve all templates
        cursor.execute("SELECT trigger_app, action_apps, complexity_score, monthly_opex, maintenance_level FROM automation_templates")
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error accessing table 'automation_templates': {e}")
        conn.close()
        return

    # Save this out to a file called deepseek_training_data.jsonl
    with open(OUTPUT_FILE, "w") as f:
        for row in rows:
            trigger_app = row["trigger_app"] or "Unknown"
            action_apps_raw = row["action_apps"]

            # Action apps are likely stored as JSON in the database
            if isinstance(action_apps_raw, str):
                try:
                    action_apps_list = json.loads(action_apps_raw)
                except json.JSONDecodeError:
                    action_apps_list = [action_apps_raw] if action_apps_raw else ["Unknown"]
            else:
                action_apps_list = action_apps_raw if action_apps_raw else ["Unknown"]

            if isinstance(action_apps_list, list):
                action_apps = ", ".join(action_apps_list)
            else:
                action_apps = str(action_apps_list)

            complexity_score = row["complexity_score"] if row["complexity_score"] is not None else 0
            monthly_opex = row["monthly_opex"] if row["monthly_opex"] is not None else 0.0
            maintenance_level = row["maintenance_level"] or "Unknown"

            # Construct JSON object using the ChatML / OpenAI message format
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
            # Append as valid JSON lines
            f.write(json.dumps(message) + "\n")

    conn.close()
    print(f"Exported {len(rows)} templates to {OUTPUT_FILE}")

if __name__ == "__main__":
    export_to_jsonl()
