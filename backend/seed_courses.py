"""
Seed CS400 Courses into Database
Run this script to populate the database with PAU CS400 courses
"""
import sys
sys.path.append('/Users/useruser/Documents/shadow-final-year/backend')

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.course import Course, UserCourse, Semester
import uuid

# CS400 Courses from the PRD
CS400_COURSES = [
    # Compulsory Courses
    {
        "code": "COS409",
        "title": "Research Methodology",
        "credits": 3,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Research design, data collection, analysis methods"
    },
    {
        "code": "CSC401",
        "title": "Algorithms and Complexity",
        "credits": 2,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Algorithm design, complexity analysis, optimization"
    },
    {
        "code": "CSC402",
        "title": "Ethics and Legal Issues",
        "credits": 2,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Professional ethics, intellectual property, privacy"
    },
    {
        "code": "CSC497",
        "title": "Final Year Project I",
        "credits": 3,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Research proposal, literature review, initial implementation"
    },
    {
        "code": "CSC498",
        "title": "Final Year Project II",
        "credits": 3,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Project completion, testing, documentation, defense"
    },
    {
        "code": "INS401",
        "title": "Project Management",
        "credits": 2,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Planning, execution, monitoring, risk management"
    },
    {
        "code": "PAU-CSC411",
        "title": "Machine Learning",
        "credits": 2,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Supervised/unsupervised learning, neural networks"
    },
    {
        "code": "PAU-CSC412",
        "title": "Survey of Programming Languages",
        "credits": 3,
        "level": "400",
        "status": "C",
        "department": "Computer Science",
        "description": "Language paradigms, design principles, comparisons"
    },

    # Elective Courses
    {
        "code": "PAU-CSC413",
        "title": "Human-Computer Interaction",
        "credits": 2,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "UI/UX design, usability testing, accessibility"
    },
    {
        "code": "PAU-CSC414",
        "title": "Deep Learning",
        "credits": 2,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "CNN, RNN, transformers, advanced neural networks"
    },
    {
        "code": "PAU-CSC415",
        "title": "Game Design and Development",
        "credits": 2,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "Game engines, graphics, physics, AI for games"
    },
    {
        "code": "PAU-CSC416",
        "title": "Computer Vision",
        "credits": 3,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "Image processing, object detection, recognition"
    },
    {
        "code": "PAU-CSC417",
        "title": "Data Science and Engineering",
        "credits": 3,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "Data pipelines, big data, visualization, analytics"
    },
    {
        "code": "PAU-CSC418",
        "title": "Cloud Computing",
        "credits": 3,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "AWS/Azure/GCP, serverless, containerization"
    },
    {
        "code": "PAU-CSC419",
        "title": "Web, Mobile & Blockchain",
        "credits": 3,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "Full-stack web, mobile apps, blockchain fundamentals"
    },
    {
        "code": "PAU-CSC420",
        "title": "Natural Language Processing",
        "credits": 3,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "Text processing, NLP models, transformers"
    },
    {
        "code": "PAU-CSC421",
        "title": "Data Management II",
        "credits": 2,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "Advanced databases, NoSQL, distributed systems"
    },
    {
        "code": "PAU-CSC422",
        "title": "Computer Networks II",
        "credits": 3,
        "level": "400",
        "status": "E",
        "department": "Computer Science",
        "description": "Advanced networking, security, protocols"
    }
]


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!\n")


def seed_courses():
    """Seed CS400 courses into the database"""
    db = SessionLocal()

    try:
        print("Seeding CS400 courses...\n")

        added_count = 0
        skipped_count = 0

        for course_data in CS400_COURSES:
            # Check if course already exists
            existing = db.query(Course).filter(Course.code == course_data["code"]).first()

            if existing:
                print(f"⏭️  Skipped: {course_data['code']} - {course_data['title']} (already exists)")
                skipped_count += 1
                continue

            # Create new course
            course = Course(
                code=course_data["code"],
                title=course_data["title"],
                credits=course_data["credits"],
                level=course_data["level"],
                status=course_data["status"],
                department=course_data["department"],
                description=course_data["description"],
                created_by="admin",
                is_approved=True
            )

            db.add(course)
            print(f"✅ Added: {course_data['code']} - {course_data['title']} ({course_data['credits']} credits)")
            added_count += 1

        db.commit()

        print(f"\n{'='*60}")
        print(f"✅ Seeding complete!")
        print(f"   - Added: {added_count} courses")
        print(f"   - Skipped: {skipped_count} courses (already existed)")
        print(f"   - Total: {added_count + skipped_count} CS400 courses")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Error seeding courses: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main function"""
    print("\n" + "="*60)
    print("🌱 Shadow - Database Initialization & Course Seeding")
    print("="*60 + "\n")

    # Create tables first
    create_tables()

    # Seed courses
    seed_courses()

    print("✅ All done! You can now start the application.\n")


if __name__ == "__main__":
    main()
