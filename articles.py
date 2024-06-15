import streamlit as st
import pandas as pd

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
    
    # Function to filter and score articles based on user preferences and profile
    def filter_and_score_articles(df, categories, interests, role, interest_field):
        df['relevance_score'] = 0
        
        # Increase score for matching categories
        for cat in categories:
            df.loc[df['description'].str.contains(cat, case=False, na=False), 'relevance_score'] += 1
        
        # Increase score for matching specific interests
        for interest in interests:
            df.loc[df['description'].str.contains(interest, case=False, na=False), 'relevance_score'] += 1
        
        # Increase score for matching role
        df.loc[df['description'].str.contains(role, case=False, na=False), 'relevance_score'] += 1
        
        # Increase score for matching interest field
        df.loc[df['description'].str.contains(interest_field, case=False, na=False), 'relevance_score'] += 1
        
        # Filter articles with a positive relevance score and sort by score
        filtered_df = df[df['relevance_score'] > 0].sort_values(by='relevance_score', ascending=False)
        return filtered_df

    # Function to generate explanation for why an article was chosen
    def generate_explanation(article, categories, interests, role, interest_field):
        reasons = []
        if any(cat.lower() in article['description'].lower() for cat in categories):
            reasons.append(f"matches your interest in categories like {', '.join(categories)}")
        if any(interest.lower() in article['description'].lower() for interest in interests):
            reasons.append(f"aligns with your specific interest in {', '.join(interests)}")
        if role.lower() in article['description'].lower():
            reasons.append(f"relates to your role as a {role}")
        if interest_field.lower() in article['description'].lower():
            reasons.append(f"is related to your current research or interest in {interest_field}")
        return reasons

    # Display user preferences and filtered articles
    if st.button("Submit"):
        st.subheader("Your Preferences")
        st.write("**Role:**", user_role)
        st.write("**Interest Field:**", user_interest_field)
        st.write("**Interest Categories:**", selected_categories + ([other_category] if other_category else []))
        st.write("**Specific Interests:**", specific_interests)
        
        # Filter and score articles based on user preferences and profile
        filtered_articles = filter_and_score_articles(articles_df, selected_categories + [other_category], specific_interests, user_role, user_interest_field)
        
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
                
                # Generate and display explanation
                explanation = generate_explanation(row, selected_categories + [other_category], specific_interests, user_role, user_interest_field)
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
