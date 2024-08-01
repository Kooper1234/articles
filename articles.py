import streamlit as st
import pandas as pd
import requests
import json
import re

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

    required_columns = ['title', 'description', 'text', 'url']
    missing_columns = [col for col in required_columns if col not in articles_df.columns]

    if missing_columns:
        st.error(f"The following required columns are missing from the uploaded file: {', '.join(missing_columns)}")
    else:
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
                        {"role": "system", "content": "Calculate the relevance score between the following user information and article information. Format your response as 'Relevance Score: [relevance score]', then on a new line, 'Title: [title]', then on a new line, 'URL: [url]', then on a new line, 'Rationale: [rationale]'"},
                        {"role": "user", "content": f"User Information: {user_info}\n\nArticle Information: {article_info}"}
                    ]
                }
                response = requests.post(api_url, headers=headers, json=data)
                response.raise_for_status()
                response_json = response.json()
                content = response_json['choices'][0]['message']['content'].strip()

                # Extract relevance score, title, url, and rationale
                score_match = re.search(r"Relevance Score: (\d+(\.\d+)?)", content)
                title_match = re.search(r"Title: (.+)", content)
                url_match = re.search(r"URL: (.+)", content)
                rationale_match = re.search(r"Rationale: (.+)", content, re.DOTALL)

                score = float(score_match.group(1)) if score_match else 0.0
                title = title_match.group(1) if title_match else "N/A"
                url = url_match.group(1) if url_match else "N/A"
                rationale = rationale_match.group(1).strip() if rationale_match else "N/A"

                return score, title, url, rationale
            except Exception as e:
                st.error(f"Error calculating relevance score: {e}")
                return 0.0, "N/A", "N/A", "N/A"

        def generate_summary(article, user_role, user_interest_field):
            try:
                if 'text' not in article:
                    raise ValueError("The 'text' field is missing in the article.")
                
                data = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": f"Generate a summary of the article focusing on information relevant to the user's research interest '{user_interest_field}'. The summary should be in a style that is most readable for a '{user_role}'."},
                        {"role": "user", "content": f"Article Title: {article['title']}\n\nArticle Description: {article['description']}\n\nArticle Text: {article['text']}"}
                    ]
                }
                response = requests.post(api_url, headers=headers, json=data)
                response.raise_for_status()
                response_json = response.json()
                return response_json['choices'][0]['message']['content'].strip()
            except Exception as e:
                st.error(f"Error generating summary: {e}")
                return ""

        # Generate user profile information
        user_profile = {
            "role": user_role,
            "interest_field": user_interest_field,
            "categories": selected_categories,
            "specific_interests": specific_interests,
            "other_category": other_category
        }
        user_info = extract_relevant_info(str(user_profile))

        results = []

        for index, row in articles_df.iterrows():
            article_info = f"Title: {row['title']}\nDescription: {row['description']}\nText: {row['text']}\nURL: {row['url']}"
            score, title, url, rationale = calculate_relevance_score(user_info, article_info)
            results.append({
                'title': title,
                'author': row.get('author', 'N/A'),
                'publisher': row.get('publisher', 'N/A'),
                'description': row['description'],
                'text': row.get('text', 'N/A'),
                'url': url,
                'image': row.get('image', ''),
                'relevance_score': score,
                'rationale': rationale
            })

        # Create a DataFrame from the results and normalize relevance score to a scale of 1 to 10
        if results:
            results_df = pd.DataFrame(results)
            max_score = results_df['relevance_score'].max()
            min_score = results_df['relevance_score'].min()
            if max_score != min_score:
                results_df['relevance_rating'] = 1 + 9 * (results_df['relevance_score'] - min_score) / (max_score - min_score)
            else:
                results_df['relevance_rating'] = 10  # If all scores are the same, set rating to 10
            results_df['relevance_rating'] = results_df['relevance_rating'].round(1)
            results_df = results_df.sort_values(by='relevance_rating', ascending=False)

            # Debug statement to show results DataFrame
            st.write("Results DataFrame after sorting by relevance rating:")
            st.dataframe(results_df.head(10))

        # Display user preferences and top 5 filtered articles
        if st.button("Submit"):
            st.subheader("Your Preferences")
            st.write("**Role:**", user_role)
            st.write("**Interest Field:**", user_interest_field)
            st.write("**Interest Categories:**", selected_categories + ([other_category] if other_category else []))
            st.write("**Specific Interests:**", specific_interests)
            
            st.subheader("Recommended Articles")
            if not results_df.empty:
                top_articles = results_df.head(5)  # Show top 5 most relevant articles

                # Debug statement to show top 5 articles
                st.write("Top 5 most relevant articles:")
                st.dataframe(top_articles)

                for index, row in top_articles.iterrows():
                    st.write(f"**Title:** {row['title']}")
                    st.write(f"**Author:** {row['author']}")
                    st.write(f"**Publisher:** {row['publisher']}")
                    st.write(f"**Description:** {row['description']}")
                    st.image(row['image'], use_column_width=True)
                    
                    # Display relevance rating
                    st.write(f"**Relevance Rating:** {row['relevance_rating']}/10")
                    
                    # Display rationale
                    st.write("**Why this article was chosen for you:**")
                    st.write(row['rationale'])
                    
                    # Display the article URL
                    st.write(f"[Read more]({row['url']})")
                    st.write("---")
                
                # Generate and display summary for the most relevant article
                most_relevant_article = top_articles.iloc[0]
                st.subheader("Summary of the Most Relevant Article")
                summary = generate_summary(most_relevant_article, user_role, user_interest_field)
                st.write(summary)
            else:
                st.write("No articles found matching your preferences.")
else:
    st.write("Please upload an Excel file to proceed.")
