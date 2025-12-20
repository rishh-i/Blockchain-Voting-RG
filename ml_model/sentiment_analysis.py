import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

class SentimentAnalysisModel:
    def __init__(self, model_path="ml_model/sentiment_model.pkl"):
        self.model_path = model_path
        self.vectoriser = None
        self.model = None

        # loads model if exists else trains new model
        if os.path.exists(model_path):
            self.load_model()
        else:
            print("No model found, training new model")
            self.train_default_model()

    def train_default_model(self):
        """
        Currently model is trained on a small dataset (50 samples for each of the 3 categories).
        This can easily be replaced by training on larger datasets e.g. from kaggle.
        """

        training_data = [
            # positive feedback examples
            ("This campaign was excellent and very inspiring", "positive"),
            ("Great candidate with wonderful ideas", "positive"),
            ("I'm very happy with this election process", "positive"),
            ("Outstanding leadership qualities demonstrated", "positive"),
            ("The best choice for our community", "positive"),
            ("Impressive campaign and clear vision", "positive"),
            ("Highly competent and trustworthy candidate", "positive"),
            ("Wonderful policies that benefit everyone", "positive"),
            ("Exceptional performance in debates", "positive"),
            ("Strong leadership and great communication", "positive"),
            ("Love the progressive approach to issues", "positive"),
            ("Perfect candidate for the position", "positive"),
            ("Amazing campaign with clear objectives", "positive"),
            ("Very satisfied with the election transparency", "positive"),
            ("Excellent representation of student interests", "positive"),
            ("Brilliant ideas for improving our university", "positive"),
            ("Fantastic engagement with students", "positive"),
            ("Really impressed with the professionalism", "positive"),
            ("Best campaign I've seen in years", "positive"),
            ("Very excited about the proposed changes", "positive"),
            ("Outstanding commitment to student welfare", "positive"),
            ("Great vision for the future", "positive"),
            ("Excellent communication throughout campaign", "positive"),
            ("Wonderful dedication and passion shown", "positive"),
            ("Very inspiring and motivational", "positive"),
            ("Brilliant proposals for campus improvements", "positive"),
            ("Fantastic track record of achievements", "positive"),
            ("Really good understanding of student needs", "positive"),
            ("Excellent problem-solving abilities", "positive"),
            ("Great experience and qualifications", "positive"),
            ("Very effective leader with proven results", "positive"),
            ("Wonderful personality and approachable", "positive"),
            ("Excellent manifesto with clear goals", "positive"),
            ("Very enthusiastic and energetic campaign", "positive"),
            ("Great potential to make positive changes", "positive"),
            ("Outstanding credentials and experience", "positive"),
            ("Brilliant speaker and communicator", "positive"),
            ("Very professional and organized", "positive"),
            ("Excellent ideas for student services", "positive"),
            ("Great focus on important issues", "positive"),
            ("Very knowledgeable about university matters", "positive"),
            ("Wonderful commitment to transparency", "positive"),
            ("Excellent accessibility to students", "positive"),
            ("Great listening skills and receptiveness", "positive"),
            ("Very thoughtful and well-planned campaign", "positive"),
            ("Outstanding integrity and honesty", "positive"),
            ("Brilliant collaborative approach", "positive"),
            ("Very inclusive and representative", "positive"),
            ("Excellent problem-identification skills", "positive"),
            ("Great teamwork and cooperation shown", "positive"),

            # negative feedback examples
            ("This campaign was disappointing and unclear", "negative"),
            ("Poor communication from the candidate", "negative"),
            ("Not impressed with the campaign promises", "negative"),
            ("Lacking leadership qualities", "negative"),
            ("Worst campaign I have seen", "negative"),
            ("Unclear policies and vague statements", "negative"),
            ("Untrustworthy candidate with bad track record", "negative"),
            ("Terrible debate performance", "negative"),
            ("Weak leadership and poor planning", "negative"),
            ("Dislike the approach to important issues", "negative"),
            ("Inadequate candidate for this position", "negative"),
            ("Awful campaign with no substance", "negative"),
            ("Very disappointed with lack of transparency", "negative"),
            ("Poor representation of student needs", "negative"),
            ("Bad policies that won't help anyone", "negative"),
            ("Horrible communication skills", "negative"),
            ("Very unprofessional behavior", "negative"),
            ("Terrible ideas that make no sense", "negative"),
            ("Disappointing lack of experience", "negative"),
            ("Very concerning attitude and approach", "negative"),
            ("Poor understanding of key issues", "negative"),
            ("Awful engagement with students", "negative"),
            ("Very unrealistic and impractical proposals", "negative"),
            ("Terrible track record of failures", "negative"),
            ("Disappointing lack of commitment", "negative"),
            ("Very poor problem-solving abilities", "negative"),
            ("Horrible leadership style", "negative"),
            ("Disappointing lack of qualifications", "negative"),
            ("Very weak manifesto with no direction", "negative"),
            ("Poor enthusiasm and energy", "negative"),
            ("Very unlikely to make any changes", "negative"),
            ("Disappointing credentials", "negative"),
            ("Terrible speaking and presentation skills", "negative"),
            ("Very disorganized and chaotic campaign", "negative"),
            ("Poor ideas for student services", "negative"),
            ("Very narrow focus ignoring major issues", "negative"),
            ("Disappointing lack of knowledge", "negative"),
            ("Very secretive and non-transparent", "negative"),
            ("Poor accessibility to students", "negative"),
            ("Very dismissive and not listening", "negative"),
            ("Terrible planning and preparation", "negative"),
            ("Disappointing lack of integrity", "negative"),
            ("Very individualistic and non-collaborative", "negative"),
            ("Poor inclusivity and representation", "negative"),
            ("Very weak problem-identification", "negative"),
            ("Disappointing lack of teamwork", "negative"),
            ("Terrible attitude towards criticism", "negative"),
            ("Very arrogant and condescending", "negative"),
            ("Poor respect for diverse opinions", "negative"),
            ("Very unprepared for responsibilities", "negative"),

            # neutral feedback examples
            ("The election process was standard", "neutral"),
            ("Campaign was average, nothing special", "neutral"),
            ("Okay candidate with some good points", "neutral"),
            ("The process could be improved", "neutral"),
            ("Mixed feelings about this candidate", "neutral"),
            ("Some policies are good, others need work", "neutral"),
            ("Average performance overall", "neutral"),
            ("Neither impressed nor disappointed", "neutral"),
            ("The campaign was fine but unremarkable", "neutral"),
            ("Acceptable candidate for the role", "neutral"),
            ("Standard election procedures followed", "neutral"),
            ("Moderate level of engagement shown", "neutral"),
            ("Reasonable policies proposed", "neutral"),
            ("Satisfactory communication level", "neutral"),
            ("Adequate understanding of issues", "neutral"),
            ("Fair representation of views", "neutral"),
            ("Decent campaign organization", "neutral"),
            ("Acceptable level of transparency", "neutral"),
            ("Moderate experience demonstrated", "neutral"),
            ("Reasonable qualifications presented", "neutral"),
            ("Standard manifesto content", "neutral"),
            ("Average debate performance", "neutral"),
            ("Satisfactory leadership shown", "neutral"),
            ("Fair approach to student concerns", "neutral"),
            ("Decent problem-solving attempts", "neutral"),
            ("Acceptable professionalism level", "neutral"),
            ("Moderate innovation in ideas", "neutral"),
            ("Reasonable accessibility to voters", "neutral"),
            ("Standard commitment level shown", "neutral"),
            ("Fair listening to feedback", "neutral"),
            ("Adequate planning evident", "neutral"),
            ("Acceptable integrity demonstrated", "neutral"),
            ("Moderate collaboration shown", "neutral"),
            ("Reasonable inclusivity efforts", "neutral"),
            ("Standard teamwork approach", "neutral"),
            ("Fair handling of criticism", "neutral"),
            ("Adequate respect for opinions", "neutral"),
            ("Reasonable preparedness level", "neutral"),
            ("Satisfactory knowledge of matters", "neutral"),
            ("Acceptable enthusiasm shown", "neutral"),
            ("Standard communication methods used", "neutral"),
            ("Fair understanding of needs", "neutral"),
            ("Adequate vision presented", "neutral"),
            ("Reasonable track record", "neutral"),
            ("Satisfactory engagement level", "neutral"),
            ("Acceptable proposal quality", "neutral"),
            ("Standard credentials displayed", "neutral"),
            ("Fair speaking abilities", "neutral"),
            ("Adequate organization shown", "neutral"),
            ("Reasonable focus on issues", "neutral"),
        ]

        # separates the texts and labels
        # each element in training_data is a tuple
        texts = [text for text, _ in training_data] # takes first element of each tuple and ignores second
        labels = [label for _, label in training_data] # takes second element of each tuple and ignores first

        # splits data into training and testing sets (80-20 split)
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )

        # intialises the TFIDF vectoriser
        self.vectoriser = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1,
            stop_words="english",
            sublinear_tf=True
        )

        # converts texts to TFIDF features
        X_train_tfidf = self.vectoriser.fit_transform(X_train)
        X_test_tfidf = self.vectoriser.transform(X_test)

        # trains model using logistic regression (classification algorithm)
        self.model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight="balanced",
            C = 1.0,
            solver="lbfgs"
        )
        self.model.fit(X_train_tfidf, y_train)

        y_pred = self.model.predict(X_test_tfidf)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"\n{'=' * 50}")
        print(f"Model training completed")
        print(f"{'=' * 50}")
        print(f"Training Accuracy: {self.model.score(X_train_tfidf, y_train):.2%}")
        print(f"Test Accuracy: {accuracy:.2%}")
        print(f"\nDetailed Classification Report:")
        print(classification_report(y_test, y_pred))
        print(f"{'=' * 50}\n")

        # saves the trained model
        self.save_model()
        print(f"Model trained and saved to {self.model_path}")

    def analyse_sentiment(self, text):
        """
        Analyses sentiment of the given text.
        Returns: (sentiment, confidence_score)
        """

        if not self.model or not self.vectoriser:
            raise ValueError("Model not trained or loaded")

        # handles empty text
        if not text or not text.strip():
            return "neutral", 0.5

        X = self.vectoriser.transform([text])

        sentiment = self.model.predict(X)[0]

        probabilities = self.model.predict_proba(X)[0]
        confidence = max(probabilities)

        return sentiment, float(confidence)

    def save_model(self):
        # saves the model and vectoriser locally
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump({
                "vectoriser": self.vectoriser,
                "model": self.model
            }, f)

    def load_model(self):
        # loads the pre-trained model
        with open(self.model_path, "rb") as f:
            data = pickle.load(f)
            self.vectoriser = data["vectoriser"]
            self.model = data["model"]
        print(f"Model loaded from {self.model_path}")