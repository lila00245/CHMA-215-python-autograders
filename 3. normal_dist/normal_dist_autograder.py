# imports
import nbformat                                                             # notebook file parsing/editing
from nbclient import NotebookClient                                         # runs notebooks like jupyter
from nbclient.exceptions import CellExecutionError as CallExecutionError    # cell crash errors

import unittest                                                             # testing framework

import os                                                                   # file/folder handling
import csv                                                                  # output grade report
import re                                                                   # filename cleanup
import builtins                                                             # protects max/min if student overwrites them
import shutil                                                               # file copying

import statistics                                                           # mean/stdev calculations
from scipy.stats import norm                                                # normal distribution functions    


# ---------------- CONFIG ----------------
# folder containing all student submissions (.ipynb files)
SUBMISSIONS_FOLDER = "3. normal_dist/submissions"

# folder where dataset used by notebooks is stored
CURRENT_FOLDER = "3. normal_dist"

# dataset file that gets injected into student notebooks before execution
INPUT_CSV = "normdist.csv"

# final output file that stores all grades + feedback
OUTPUT_CSV = "3. normal_dist/normal_dist_grade_report.csv"

# this is the correct dataset students are supposed to load
# used to verify they loaded and processed data correctly
EXPECTED_DATA_LIST = [36.7, 38.8, 38.4, 36.9, 36.6, 35.6, 38.0, 38.4, 37.5, 37.3, 37.0, 38.0, 37.2, 36.9, 36.7, 36.0, 37.1, 35.3, 38.7, 35.9, 36.8, 35.6, 37.3, 36.2, 35.9, 35.9, 38.1, 38.1, 36.3, 38.1, 38.2, 38.0, 38.1, 36.3, 37.0, 35.3, 35.6, 36.3, 37.6, 37.0, 37.6, 38.2, 36.8, 37.4, 35.8, 38.4, 38.2, 34.0, 38.2, 37.4, 37.0, 37.4, 38.4, 38.2, 36.9, 37.3, 38.2, 36.8, 38.4, 37.1, 36.3, 36.7, 36.2, 39.4, 36.4, 38.6, 37.9, 38.0, 37.8, 37.4, 36.6, 35.9, 34.1, 37.0, 37.6, 37.8, 35.9, 35.3, 34.8, 36.9, 37.1, 36.9, 36.7, 37.1, 36.5, 37.2, 38.0, 37.3, 37.3, 37.1, 38.4, 38.6, 37.7, 36.3, 36.6, 37.6, 38.2, 36.9, 36.7, 39.1]


# points per test
TEST_POINTS = {
    "test_data_list": 2,
    "test_avg": 1,
    "test_sd": 1,
    "test_prob_leq_39": 1,
    "test_prob_geq_39": 1, 
    "test_prob_leq_38_5": 1,
    "test_students_geq_39": 1,
    "test_prob_leq_36": 1,
    "test_prob_36_to_38_5": 1,
    "test_students_36_to_38_5": 1,
    "test_students_leq_36": 1
}

# human readable descriptions for students
# feedback of what they did wrong
TEST_DESCRIPTIONS = {
    "test_data_list": "data_list value(s) are incorrect",
    "test_avg": "avg value is incorrect",
    "test_sd": "sd value is incorrect",
    "test_prob_leq_39": "prob_leq_39 value is incorrect",
    "test_prob_geq_39": "prob_geq_39 value is incorrect", 
    "test_students_geq_39": "students_geq_39 value is incorrect",
    "test_prob_leq_38_5": "prob_leq_38_5 value is incorrect",
    "test_prob_leq_36": "prob_leq_36 value is incorrect",
    "test_prob_36_to_38_5": "prob_36_to_38_5 value is incorrect",
    "test_students_36_to_38_5": "students_36_to_38_5 value is incorrect",
    "test_students_leq_36": "students_leq_36 value is incorrect"
}

BONUS_POINTS = {
    "test_z_score": 0.5
}

# feedback for what they got correct / bonus points for
BONUS_DESCRIPTIONS = {
    "test_z_score": "you found the correct z_score value"
}


# ---------------- TEST CASES ----------------
class StudentTests(unittest.TestCase):
    """
    this class defines all grading rules.

    each function is one grading check:
    - verify variable exists
    - verify type is correct
    - verify value matches expected math/stat result

    if a test fails, points are deducted
    """
    # checks that the data list was loaded correctly.
    def test_data_list(self):
        self.assertIn("data_list", globals())
        self.assertIsInstance(data_list, list)
        self.assertEqual(data_list, EXPECTED_DATA_LIST)

    # checks that the average was calculated correctly.
    def test_avg(self):
        self.assertIn("data_list", globals())
        self.assertIn("avg", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(avg, float)

        expected = statistics.mean(data_list)
        self.assertAlmostEqual(avg, expected, places=5)

    # checks that the sample standard deviation was calculated correctly.
    def test_sd(self):
        self.assertIn("data_list", globals())
        self.assertIn("sd", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(sd, float)

        expected = statistics.stdev(data_list)
        self.assertAlmostEqual(sd, expected, places=5)

    # checks that the probability of X <= 39 was calculated correctly.
    def test_prob_leq_39(self):
        self.assertIn("avg", globals())
        self.assertIn("sd", globals())
        self.assertIn("prob_leq_39", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(sd, float)
        self.assertIsInstance(prob_leq_39, float)

        expected = norm.cdf(39, avg, sd)
        self.assertAlmostEqual(prob_leq_39, expected, places=5)

    # checks that the probability of X >= 39 was calculated correctly.
    def test_prob_geq_39(self):
        self.assertIn("avg", globals())
        self.assertIn("sd", globals())
        self.assertIn("prob_geq_39", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(sd, float)
        self.assertIsInstance(prob_geq_39, float)

        expected = 1 - norm.cdf(39, avg, sd)
        self.assertAlmostEqual(prob_geq_39, expected, places=5)

    # checks that the number of students with X >= 39 was calculated correctly.
    def test_students_geq_39(self):
        self.assertIn("prob_geq_39", globals())
        self.assertIn("students_geq_39", globals())
        self.assertIsInstance(prob_geq_39, float)
        self.assertIsInstance(students_geq_39, int)

        expected = round(prob_geq_39 * 20000)
        self.assertEqual(students_geq_39, expected)

    # checks that the probability of X <= 38.5 was calculated correctly.
    def test_prob_leq_38_5(self):
        self.assertIn("avg", globals())
        self.assertIn("sd", globals())
        self.assertIn("prob_leq_38_5", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(sd, float)
        self.assertIsInstance(prob_leq_38_5, float)

        expected = norm.cdf(38.5, avg, sd)
        self.assertAlmostEqual(prob_leq_38_5, expected, places=5)

    # checks that the probability of X <= 36 was calculated correctly.
    def test_prob_leq_36(self):
        self.assertIn("avg", globals())
        self.assertIn("sd", globals())
        self.assertIn("prob_leq_36", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(sd, float)
        self.assertIsInstance(prob_leq_36, float)

        expected = norm.cdf(36, avg, sd)
        self.assertAlmostEqual(prob_leq_36, expected, places=5)

    # checks that the probability of 36 <= X <= 38.5 was calculated correctly.
    def test_prob_36_to_38_5(self):
        self.assertIn("prob_leq_36", globals())
        self.assertIn("prob_leq_38_5", globals())
        self.assertIn("prob_36_to_38_5", globals())
        self.assertIsInstance(prob_leq_36, float)
        self.assertIsInstance(prob_leq_38_5, float)
        self.assertIsInstance(prob_36_to_38_5, float)

        expected = prob_leq_38_5 - prob_leq_36
        self.assertAlmostEqual(prob_36_to_38_5, expected, places=5)

    # checks that the number of students with 36 <= X <= 38.5 was calculated correctly.
    def test_students_36_to_38_5(self):
        self.assertIn("prob_36_to_38_5", globals())
        self.assertIn("students_36_to_38_5", globals())
        self.assertIsInstance(prob_36_to_38_5, float)
        self.assertIsInstance(students_36_to_38_5, int)

        expected = round(prob_36_to_38_5 * 20000)
        self.assertEqual(students_36_to_38_5, expected)

    # checks that the number of students with X <= 36 was calculated correctly.
    def test_students_leq_36(self):
        self.assertIn("prob_leq_36", globals())
        self.assertIn("students_leq_36", globals())
        self.assertIsInstance(prob_leq_36, float)
        self.assertIsInstance(students_leq_36, int)

        expected = round(prob_leq_36 * 20000)
        self.assertEqual(students_leq_36, expected)

    # checks that the z-score was calculated correctly.
    def test_z_score(self):
        self.assertIn("avg", globals())
        self.assertIn("sd", globals())
        self.assertIn("z_score", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(sd, float)
        self.assertIsInstance(z_score, float)

        expected = (39 - avg) / sd
        self.assertAlmostEqual(z_score, expected, places=5)


# ---------------- EXECUTION ----------------
def execute_notebook(path):
    """
    runs a student notebook safely and extracts all variables created.

    this function:
    1. loads the notebook file
    2. injects a fake google.colab upload (so code doesn't break locally)
    3. copies required dataset into working directory
    4. executes notebook cells in order
    5. builds a namespace of all variables created by student code

    even if the notebook crashes:
    - execution continues safely
    - partial results are still collected
    """
    
    with open(path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # injects fake google colab file upload so notebooks don't break outside colab    
    mock_code = """
import sys, types
google_module = types.ModuleType("google")
colab_module = types.ModuleType("google.colab")
files_module = types.ModuleType("google.colab.files")

def fake_upload():
    print(f"[Autograder] Mock upload called — using local normdist.csv")
    return {"normdist.csv": b""}

files_module.upload = fake_upload
colab_module.files = files_module
google_module.colab = colab_module

sys.modules["google"] = google_module
sys.modules["google.colab"] = colab_module
sys.modules["google.colab.files"] = files_module
"""

    # copies dataset into current directory so student code can load it normally
    nb.cells.insert(0, nbformat.v4.new_code_cell(mock_code))

    try:
        shutil.copy(
            os.path.join(CURRENT_FOLDER, INPUT_CSV),
            INPUT_CSV
        )
    except Exception as e:
        print(f"[warning] csv copy failed: {e}")


    # runs notebook in isolated kernel environment
    # if student code crashes, we catch it so autograder doesn't stop
    client = NotebookClient(nb, timeout=60, kernel_name="python3")

    try:
        client.execute()
    except Exception as e:
        print(f"[warning] notebook crashed: {e}")


    # rebuild namespace safely and retrieve all code cell information
    ns = {}

    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue

        try:
            exec(cell.source, ns)
        except Exception as e:
            print(f"[cell {i} error] {e}")

    return ns


# ---------------- GRADING ----------------
def grade_notebook(path):
    """
    runs a full grading cycle for one student notebook:

    1. execute notebook safely
    2. collect variables produced by student
    3. run unit tests on those variables
    4. track which tests passed/failed
    5. compute final score
    6. return structured results for reporting
    """    
    
    student_ns = execute_notebook(path)
    
    # if notebook failed completely, still return empty namespace instead of crashing grader
    if student_ns is None:
        return 0, [], []
    
    globals().update(student_ns)

    # loads unit tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(StudentTests)

    # creates failure and bonus pts lists
    failures_info = []
    passed_bonus_tests = []

    # class to add failures and errors 
    class CaptureResults(unittest.TextTestResult):
        def addFailure(self, test, err):
            test_name = test._testMethodName

            # skip adding bonus tests to failures
            if test_name not in BONUS_POINTS:
                failures_info.append({
                    "test": test_name,
                    "points_lost": TEST_POINTS.get(test_name, 0)
                })
            super().addFailure(test, err)

        def addError(self, test, err):
            test_name = test._testMethodName
            if test_name not in BONUS_POINTS:
                failures_info.append({
                    "test": test_name,
                    "points_lost": TEST_POINTS.get(test_name, 0)
                })
            super().addError(test, err)
        
        def addSuccess(self, test):
            test_name = test._testMethodName
            if test_name in BONUS_POINTS:
                passed_bonus_tests.append(test_name)
            super().addSuccess(test)
    
    # runs unit tests 
    runner = unittest.TextTestRunner(verbosity=0, resultclass=CaptureResults)
    runner.run(suite)

    # base scoring
    total_points = sum(TEST_POINTS.values())
    points_lost = sum(f["points_lost"] for f in failures_info)
    score = builtins.max(0, total_points - points_lost) 

    # bonus scoring
    bonus_awarded = sum(BONUS_POINTS[t] for t in passed_bonus_tests)

    # final percentage
    final_score = (score + bonus_awarded) / total_points * 100

    # return everything
    return final_score, failures_info, passed_bonus_tests, bonus_awarded


# ---------------- MAIN ----------------
def main():
    """
    processes all student submissions:

    for each notebook:
    - grade it
    - generate feedback
    - store results

    finally:
    - export everything to a CSV file for easy viewing in Excel
    """

    total_points_possible = sum(TEST_POINTS.values())
    results = []

    # loops through each submission in folder
    for file in os.listdir(SUBMISSIONS_FOLDER):
        if file.endswith(".ipynb"):
            student_name = re.sub(r"\.ipynb$", "", file)    # strips .ipynb
            path = os.path.join(SUBMISSIONS_FOLDER, file)
            print(f"grading {student_name}...")

            # grade the notebook
            score_percent, failures_info, passed_bonus_tests, bonus_awarded = grade_notebook(path)

            points_lost = sum(f["points_lost"] for f in failures_info)
            points_earned = (total_points_possible - points_lost) + bonus_awarded

            # failures breakdown
            if failures_info:
                breakdown = "\r\n".join(
                    f"{TEST_DESCRIPTIONS.get(f['test'], f['test'])} (-{f['points_lost']} pts)"
                    for f in failures_info
                )
            else:
                breakdown = "all required tests passed, good job!!"

            # bonus breakdown
            if passed_bonus_tests:
                bonus_msgs = "\r\n".join(
                    f"{BONUS_DESCRIPTIONS.get(b, b)} (+{BONUS_POINTS[b]} pts)"
                    for b in passed_bonus_tests
                )
                breakdown += "\r\nBONUS:\r\n" + bonus_msgs
            
            # adds dictionary of all info to results 
            results.append({
                "student": student_name,
                "total_points": total_points_possible,
                "points_earned": points_earned,
                "points_lost": points_lost,
                "score_percent": round(score_percent, 2),
                "feedback": breakdown
            })

    # removing extra csv file created
    if os.path.exists(f"{INPUT_CSV}"):
        os.remove(f"{INPUT_CSV}")

    # write results to CSV file
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["student", "total_points", "points_earned", "points_lost", "score_percent", "feedback"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in results:
            writer.writerow(row)
    
    print(f"\n\nGrading complete. \nResults saved to {OUTPUT_CSV}. \nGo to your files folder and open in excel for a better view. \n\n")


# ---------------- RUN ----------------
if __name__ == "__main__":
    main()