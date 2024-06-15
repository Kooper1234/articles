import streamlit as st
import pandas as pd

# Load the articles database
file_path = '/mnt/data/test article database.xlsx'
articles_df = pd.read_excel(uploaded_file)

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

# Function to filter articles based on user preferences and profile
def filter_articles(df, categories, interests, role, interest_field):
    filtered_df = df[df['description'].str.contains('|'.join(categories + interests + [role, interest_field]), case=False, na=False)]
    return filtered_df

# Display user preferences and filtered articles
if st.button("Submit"):
    st.subheader("Your Preferences")
    st.write("**Role:**", user_role)
    st.write("**Interest Field:**", user_interest_field)
    st.write("**Interest Categories:**", selected_categories + ([other_category] if other_category else []))
    st.write("**Specific Interests:**", specific_interests)
    
    # Filter articles based on user preferences and profile
    filtered_articles = filter_articles(articles_df, selected_categories + [other_category], specific_interests, user_role, user_interest_field)
    
    st.subheader("Recommended Articles")
    if not filtered_articles.empty:
        for index, row in filtered_articles.iterrows():
            st.write(f"**Title:** {row['title']}")
            st.write(f"**Author:** {row['author/0']}")
            st.write(f"**Publisher:** {row['publisher']}")
            st.write(f"**Description:** {row['description']}")
            st.write(f"[Read more]({row['url']})")
            st.image(row['image'], use_column_width=True)
            st.write("---")
    else:
        st.write("No articles found matching your preferences.")
else:
    st.write("Please fill out the form and submit to get recommendations.")
