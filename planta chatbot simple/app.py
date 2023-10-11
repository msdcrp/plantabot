from flask import Flask, request, jsonify, render_template
import openai
from onboarding_questions import onboarding_questions
from pymongo import MongoClient

app = Flask(__name__)

# Initialize OpenAI with the secret key
openai.api_key = "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"

# Initialize MongoDB client
mongo_client = MongoClient("mongodb+srv://mikescottodc:Emmesdcrp@cluster0.n3ekxrw.mongodb.net/")  # Update the connection string

# Define the MongoDB database and collection
db = mongo_client["Cluster0"]  # Replace with your desired database name
user_collection = db["users"]  # Collection to store user profiles

# Global variables
current_question_index = 0
user_data = {}
post_onboarding_state = ""

@app.route("/")
def index():
    global current_question_index
    current_question_index = 0
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global current_question_index, user_data, post_onboarding_state

    user_message = request.json["message"]

    # Handle onboarding questions
    if current_question_index < len(onboarding_questions):
        user_data[onboarding_questions[current_question_index]] = user_message
        current_question_index += 1

        # Check if all onboarding questions have been answered
        if current_question_index >= len(onboarding_questions):
            # Generate a meal plan based on the user's data
            meal_plan = generate_meal_plan(user_data)
            post_onboarding_state = "ask_email_or_revise"
            return jsonify(reply=meal_plan)

        # Return the next onboarding question
        return jsonify(reply=onboarding_questions[current_question_index])

    # Handle post-onboarding interactions
    elif post_onboarding_state == "ask_email_or_revise":
        if "email" in user_message:
            # Here, you can integrate functionality to send the email
            post_onboarding_state = ""  # Clear the state
            return jsonify(reply="Sure! Please provide your email address.")
        elif "revise" in user_message:
            post_onboarding_state = "new_plan_preferences"  # Set state to revise the plan
            return jsonify(reply="Great! What changes would you like to make to the plan?")

    # Handle storing user data in MongoDB
    elif post_onboarding_state == "store_user_data":
        user_data["meal_plan"] = request.json["meal_plan"]
        user_collection.insert_one(user_data)
        post_onboarding_state = ""  # Clear the state
        return jsonify(reply="Thank you! Your meal plan has been stored in our database.")

    else:
        return jsonify(reply="I'm sorry, I didn't understand that. Can you please rephrase your question?")


def generate_meal_plan(user_data):
    """Generates a 7-day meal plan based on the user's data."""
    
    # Check for allergens
    allergens = user_data['Do you have any allergies or food sensitivities?'].lower().split(", ")
    allergen_text = " and does not include " + ", ".join(allergens) if allergens else ""
    
    # Base prompt
    base_prompt = (f"Create a vegan meal plan tailored for {user_data['What is your name?']}, a {user_data['What is your gender?']} aged {user_data['How old are you?']}. "
                   f"{user_data['What is your name?']} has a goal to {user_data['What is your dietary goal (e.g., weight loss, weight gain, muscle building, maintenance)?']}, is {user_data['What is your activity level (e.g., sedentary, lightly active, moderately active, very active)?']} and eats {user_data['How many meals do you typically eat per day?']} meals a day. "
                   f"The meal plan should include ingredients and directions for each meal{allergen_text}, and should be suitable for someone with their activity level and age.")
    
    # Generate a meal plan for each day
    meal_plan = ""
    for day in range(1, 8):
        # Meal categorization
        meal_categories = ["Breakfast", "Lunch", "Dinner"]
        
        day_prompt = (base_prompt + f" Provide a detailed meal plan for Day {day} with {meal_categories[0]}, {meal_categories[1]}, and {meal_categories[2]} options, "
              "each with a list of ingredients followed by directions.")
        try:
            response = openai.Completion.create(model="text-davinci-003", prompt=day_prompt, max_tokens=1000)
            meal_plan += f"<h3>Day {day} Vegan Meal Plan for {user_data['What is your name?']}</h3><br>"
            meal_plan += response.choices[0].text.strip().replace("\n", "<br>") + "<br><br>"
        except openai.error.APIError as e:
            print(f"OpenAI API Error on Day {day}: {e}")
            meal_plan += f"<h3>Day {day} Vegan Meal Plan for {user_data['What is your name?']}</h3><br>"
            meal_plan += "Sorry, there was an error generating the meal plan for this day. Please try again later.<br><br>"
    
    meal_plan += (f"<i>Note: Ensure {user_data['What is your name?']} drinks plenty of water throughout the day. "
                  f"This meal plan is designed to provide a balance of macronutrients and micronutrients suitable for someone who is {user_data['What is your activity level (e.g., sedentary, lightly active, moderately active, very active)?']} and aims to {user_data['What is your dietary goal (e.g., weight loss, weight gain, muscle building, maintenance)?']}. "
                  f"However, individual needs can vary, so it's essential to monitor how {user_data['What is your name?']} feels and adjust the portions or ingredients as needed. "
                  f"If {user_data['What is your name?']} has specific health concerns or dietary restrictions, it would be best to consult with a nutritionist or dietitian for a personalized plan.</i>")
    
    return meal_plan

if __name__ == "__main__":
    app.run(debug=True)
