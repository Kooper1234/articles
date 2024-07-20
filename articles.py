import streamlit as st
import pandas as pd
import requests
import json

# Initialize OpenAI API key
openai_api_key = st.secrets["OPENAI_KEY"]
api_url = "https://api.openai.com/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}"
}

# Set the title of the app
st.title("Personalized Article Recommendation")

# User Profile Information
st.header("Tell Us About Yourself")
user_role = st.selectbox("Which best describes you?", ["High School Student", "College Student", "Researcher", "Field Specialist", "Hobbyist", "Other"])
user_interest_field = st.text_input("What are you currently interested in or researching?")

# Interest Categories
st.header("Interest Categories")
categories = ["Technology", "Business", "Health", "Sports", "Entertainment", "Science", "Politics"]
selected_categories = st.multiselect("Which of the following categories are you interested in? (You can select multiple)", categories)
other_category = st.text_input("Other category (please specify):")

# Specific Interests
st.header("Specific Interests")
specific_interests = []
for i, category in enumerate(selected_categories):
    interest = st.text_input(f"Specify any particular interests within {category}:", key=f"specific_interest_{i}")
    specific_interests.append(interest)

# Upload the articles database
st.header("Upload Articles Database")
uploaded_file = st.file_uploader("Upload an Excel file with articles", type=["xlsx"])

if uploaded_file is not None:
    articles_df = pd.read_excel(uploaded_file)
    
    # Display the dataframe to understand its structure
    st.write("Loaded Articles:")
    st.dataframe(articles_df.head())

    def extract_relevant_info(text):
        try:
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Extract the key information from the following text."},
                    {"role": "user", "content": text}
                ]
            }
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            return response_json['choices'][0]['message']['content'].strip()
        except Exception as e:
            st.error(f"Error extracting information: {e}")
            return ""

    def calculate_relevance_score(user_info, article_info):
        try:
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Calculate the relevance score between the following user information and article information."},
                    {"role": "user", "content": f"User Information: {user_info}\n\nArticle Information: {article_info}\n\nRelevance Score (0-10):"}
                ]
            }
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            response_json = response.json()
            return str(response_json['choices'][0]['message']['content'].strip())
        except Exception as e:
            st.error(f"Error calculating relevance score: {e}")
            return 0.0

    # Generate user profile information
    user_profile = {
        "role": user_role,
        "interest_field": user_interest_field,
        "categories": selected_categories,
        "specific_interests": specific_interests,
        "other_category": other_category
    }
    user_info = extract_relevant_info(str(user_profile))

    articles_df['relevance_score'] = articles_df.apply(
        lambda row: calculate_relevance_score(
            user_info,
            extract_relevant_info(f"Title: {row['title']}\nDescription: {row['description']}\nText: {row['text']}")
        ), axis=1
    )

    # Normalize relevance score to a scale of 1 to 10
    if not articles_df.empty:
        max_score = articles_df['relevance_score'].max()
        min_score = articles_df['relevance_score'].min()
        if max_score != min_score:
            articles_df['relevance_rating'] = 1 + 9 * (articles_df['relevance_score'] - min_score) / (max_score - min_score)
        else:
            articles_df['relevance_rating'] = 10  # If all scores are the same, set rating to 10
        articles_df['relevance_rating'] = articles_df['relevance_rating'].round(1)
        articles_df = articles_df.sort_values(by='relevance_rating', ascending=False)

    # Function to generate explanation for why an article was chosen
    def generate_explanation(article, user_profile):
        reasons = []
        profile_terms = extract_relevant_info(str(user_profile)).split()
        content = article['title'] + " " + article['description'] + " " + article['text']
        for term in profile_terms:
            if term in content:
                reasons.append(f"matches the term '{term}'")
        return reasons

    # Display user preferences and filtered articles
    if st.button("Submit"):
        st.subheader("Your Preferences")
        st.write("**Role:**", user_role)
        st.write("**Interest Field:**", user_interest_field)
        st.write("**Interest Categories:**", selected_categories + ([other_category] if other_category else []))
        st.write("**Specific Interests:**", specific_interests)
        
        st.subheader("Recommended Articles")
        if not articles_df.empty:
            top_articles = articles_df.head(10)  # Show top 10 most relevant articles
            for index, row in top_articles.iterrows():
                st.write(f"**Title:** {row['title']}")
                st.write(f"**Author:** {row['author']}")
                st.write(f"**Publisher:** {row['publisher']}")
                st.write(f"**Description:** {row['description']}")
                st.write(f"[Read more]({row['url']})")
                st.image(row['image'], use_column_width=True)
                
                # Display relevance rating
                st.write(f"**Relevance Rating:** {row['relevance_rating']}/10")
                
                # Generate and display explanation
                explanation = generate_explanation(row, user_profile)
                if explanation:
                    st.write("**Why this article was chosen for you:**")
                    st.write(f"This article {' and '.join(explanation)}.")
                else:
                    st.write("**Why this article was chosen for you:**")
                    st.write("This article matches your profile and interests.")
                st.write("---")
        else:
            st.write("No articles found matching your preferences.")
else:
    st.write("Please upload an Excel file to proceed.")
