from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models.feedback import Feedback
from models.election import Election
from database import db

feedback_bp = Blueprint("feedback", __name__)

@feedback_bp.route("/submit/<int:election_id>", methods=["GET", "POST"])
@login_required
def submit_feedback(election_id):
    # users can submit anonymous feedback for an election
    election = Election.query.get_or_404(election_id)

    if request.method == "POST":
        feedback_text = request.form.get("feedback_text", "").strip()

        if not feedback_text:
            flash("Enter feedback before submitting.", "error")
            return render_template("submit_feedback.html", election=election)

        if len(feedback_text) < 10 or len(feedback_text) > 1000:
            flash("Feedback must be between 10 to 1000 characters long.", "error")
            return render_template("submit_feedback.html", election=election)

        try:
            # try to analyse sentiment using ml model
            sentiment, confidence = current_app.sentiment_analyser.analyse_sentiment(feedback_text)

            # adds feedback to database
            feedback = Feedback(
                election_id=election.id,
                feedback_text=feedback_text,
                sentiment=sentiment,
                confidence=confidence
            )
            db.session.add(feedback)
            db.session.commit()
            flash("Feedback submitted successfully.", "success")
            return redirect(url_for("voting.dashboard"))

        except Exception as e:
            db.session.rollback()
            print(f"Error submitting feedback: {e}")
            flash("An error occurred", "error")

    return render_template("submit_feedback.html", election=election)

def counts(feedbacks):
    # helper function to count sentiment types
    positive = sum(1 for f in feedbacks if f.sentiment == "positive")
    negative = sum(1 for f in feedbacks if f.sentiment == "negative")
    neutral = sum(1 for f in feedbacks if f.sentiment == "neutral")
    return positive, negative, neutral


#admin routes below to view feedback for an election

@feedback_bp.route("/admin/view/<int:election_id>")
@login_required
def view_feedback(election_id):

    if not current_user.is_admin:
        flash("Admin access required", "error")
        return redirect(url_for("voting.dashboard"))

    election = Election.query.get_or_404(election_id)
    feedbacks = Feedback.query.filter_by(election_id=election_id).order_by(Feedback.created_at.desc()).all()

    # statistics of sentiment analysis
    total_feedback = len(feedbacks)
    positive_count, negative_count, neutral_count = counts(feedbacks)

    avg_confidence = sum(f.sentiment_score for f in feedbacks) / total_feedback if total_feedback > 0 else 0

    stats = {
        "total": total_feedback,
        "positive": positive_count,
        "negative": negative_count,
        "neutral": neutral_count,
        "positive_percent": round((positive_count / total_feedback * 100) if total_feedback > 0 else 0, 1),
        "negative_percent": round((negative_count / total_feedback * 100) if total_feedback > 0 else 0, 1),
        "neutral_percent": round((neutral_count / total_feedback * 100) if total_feedback > 0 else 0, 1),
        "avg_confidence": round(avg_confidence, 2)
    }

    return render_template("admin_feedback.html", election=election, feedbacks=feedbacks, stats=stats)


@feedback_bp.route("/admin/all")
@login_required
def view_all_feedback():
    #admin route to view summary of feedback across all elections
    if not current_user.is_admin:
        flash("Admin access required", "error")
        return redirect(url_for("voting.dashboard"))

    elections = Election.query.all()
    feedback_data = []

    for election in elections:
        feedback_count = Feedback.query.filter_by(election_id=election.id).count()
        if feedback_count > 0:
            feedbacks = Feedback.query.filter_by(election_id=election.id).all()
            positive, negative, neutral = counts(feedbacks)

            feedback_data.append({
                "election": election,
                "total": feedback_count,
                "positive": positive,
                "negative": negative,
                "neutral": neutral
            })

    return render_template("admin_all_feedback.html", feedback_data=feedback_data)