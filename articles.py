import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
    
    # Function to preprocess and score articles based on user input using TF-IDF and cosine similarity
    def preprocess_and_score_articles(df, user_profile):
        df['content'] = df['title'] + " " + df['description'] + " " + df['text']
        documents = df['content'].tolist()
        
        # Include user profile as a document
        user_document = " ".join(user_profile)
        documents.append(user_document)
        
        # Compute TF-IDF
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # Compute cosine similarity between the user profile and articles
        cosine_similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
        
        df['relevance_score'] = cosine_similarities[0]
        
        # Normalize relevance score to a scale of 1 to 10
        if not df.empty:
            max_score = df['relevance_score'].max()
            min_score = df['relevance_score'].min()
            if max_score != min_score:
                df['relevance_rating'] = 1 + 9 * (df['relevance_score'] - min_score) / (max_score - min_score)
            else:
                df['relevance_rating'] = 10  # If all scores are the same, set rating to 10
            df['relevance_rating'] = df['relevance_rating'].round(1)
            df = df.sort_values(by='relevance_rating', ascending=False)
        
        return df

    # Function to generate explanation for why an article was chosen
    def generate_explanation(article, user_profile):
        reasons = []
        profile_terms = user_profile.split()
        content = article['content'].lower()
        for term in profile_terms:
            if term in content:
                reasons.append(f"matches the term '{term}'")
        return reasons

    # Display user preferences and filtered articles
    if st.button("Submit"):
        st.subheader("Your Preferences")
        user_profile = [user_role, user_interest_field] + selected_categories + specific_interests + [other_category]
        user_profile = [item for item in user_profile if item]  # Remove empty strings
        st.write("**User Profile:**", ", ".join(user_profile))
        
        # Preprocess and score articles based on user preferences and profile
        filtered_articles = preprocess_and_score_articles(articles_df, user_profile)
        
        st.subheader("Recommended Articles")
        if not filtered_articles.empty:
            top_articles = filtered_articles.head(10)  # Show top 10 most relevant articles
            for index, row in top_articles.iterrows():
                st.write(f"**Title:** {row['title']}")
                st.write(f"**Author:** {row['author/0']}")
                st.write(f"**Publisher:** {row['publisher']}")
                st.write(f"**Description:** {row['description']}")
                st.write(f"[Read more]({row['url']})")
                st.image(row['image'], use_column_width=True)
                
                # Display relevance rating
                st.write(f"**Relevance Rating:** {row['relevance_rating']}/10")
                
                # Generate and display explanation
                explanation = generate_explanation(row, " ".join(user_profile))
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
