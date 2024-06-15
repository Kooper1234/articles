import streamlit as st
import pandas as pd

# Set the title of the app
st.title("Article and News Preference Survey")

# Upload the articles database
uploaded_file = st.file_uploader("Upload an Excel file with articles", type=["xlsx"])

if uploaded_file is not None:
    articles_df = pd.read_excel(uploaded_file)
    
    # Display the dataframe to understand its structure
    st.write("Loaded Articles:")
    st.dataframe(articles_df.head())

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

    # Preferred Sources
    st.header("Preferred Sources")
    preferred_sources = []
    for i in range(3):
        source = st.text_input(f"Preferred source {i+1}:", key=f"preferred_source_{i}")
        if source:
            preferred_sources.append(source)

    # Frequency
    st.header("Frequency")
    frequency_options = ["Daily", "Weekly", "As they are published", "Other (please specify)"]
    selected_frequency = st.radio("How often would you like to receive new articles?", frequency_options)
    if selected_frequency == "Other (please specify)":
        selected_frequency = st.text_input("Please specify the frequency:")

    # Content Type
    st.header("Content Type")
    content_types = ["News articles", "Opinion pieces", "Research reports", "Interviews"]
    selected_content_types = st.multiselect("What type of content do you prefer? (You can select multiple)", content_types)
    other_content_type = st.text_input("Other content type (please specify):")

    # Function to filter articles based on user preferences
    def filter_articles(df, categories, interests):
        filtered_df = df[df['description'].str.contains('|'.join(categories + interests), case=False, na=False)]
        return filtered_df

    # Display user preferences and filtered articles
    if st.button("Submit"):
        st.subheader("Your Preferences")
        st.write("**Interest Categories:**", selected_categories + ([other_category] if other_category else []))
        st.write("**Specific Interests:**", specific_interests)
        st.write("**Preferred Sources:**", preferred_sources)
        st.write("**Frequency:**", selected_frequency)
        st.write("**Content Type:**", selected_content_types + ([other_content_type] if other_content_type else []))
        
        # Filter articles based on user preferences
        filtered_articles = filter_articles(articles_df, selected_categories + [other_category], specific_interests)
        
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
    st.write("Please upload an Excel file to proceed.")
