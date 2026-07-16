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
from scipy.stats import t                                                   # t.ppf function for t_inv  
import math                                                                 # math functions


# ---------------- CONFIG ----------------
# folder containing all student submissions (.ipynb files)
SUBMISSIONS_FOLDER = "case1/submissions"

# folder where dataset used by notebooks is stored
CURRENT_FOLDER = "case1"

# dataset file that gets injected into student notebooks before execution
INPUT_CSV = "case1.csv"

# final output file that stores all grades + feedback
OUTPUT_CSV = "case1/case1_grade_report.csv"

# this is the correct dataset students are supposed to load
# used to verify they loaded and processed data correctly
EXPECTED_DATA_LIST = [9.215, 11.228, 8.642, 10.334, 10.282, 11.36, 10.539, 11.506, 10.396] 
EXPECTED_RIGHT_ANSWER = 11.3

# points per test
TEST_POINTS = {
    "test_file_read": 2,
    "test_x_bar": 1,
    "test_s": 1,
    "test_n": 1,    
    "test_t_table": 1,    
    "test_lower_end": 2,
    "test_upper_end": 2, 
    "test_answer_included": 1,
}

# human readable descriptions for students
# feedback of what they did wrong
TEST_DESCRIPTIONS = {
    "test_file_read": "right_answer or data_list value(s) are incorrect",
    "test_x_bar": "x_bar value is incorrect",
    "test_s": "s value is incorrect",
    "test_n": "n value is incorrect",    
    "test_t_table": "t_table value is incorrect",    
    "test_lower_end": "lower_end value is incorrect",
    "test_upper_end": "upper_end value is incorrect", 
    "test_answer_included": "answer_included value is incorrect",
}

BONUS_POINTS = {
    "test_bonus_answer_included": 0.5
}

# feedback for what they got correct / bonus points for
BONUS_DESCRIPTIONS = {
    "test_bonus_answer_included": "you used comparison operators to find answer_included"
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

    # checks that the data was read correctly into a list
    def test_file_read(self):
        self.assertIn("right_answer", globals())
        self.assertIn("data_list", globals())
        self.assertIsInstance(right_answer, float)
        self.assertIsInstance(data_list, list)

        self.assertEqual(right_answer, EXPECTED_RIGHT_ANSWER)
        self.assertEqual(data_list, EXPECTED_DATA_LIST)


    # checks that the sample mean was calculated correctly
    def test_x_bar(self):
        self.assertIn("data_list", globals())
        self.assertIn("x_bar", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(x_bar, float)

        expected = statistics.mean(data_list)
        self.assertAlmostEqual(x_bar, expected, places=5)

    # checks that the sample standard deviation was calculated correctly
    def test_s(self):
        self.assertIn("data_list", globals())
        self.assertIn("s", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(s, float)

        expected = statistics.stdev(data_list)
        self.assertAlmostEqual(s, expected, places=5)

    # checks that the sample size was calculated correctly
    def test_n(self):
        self.assertIn("data_list", globals())
        self.assertIn("n", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(n, int)

        expected = len(data_list)
        self.assertEqual(n, expected)

    # checks that the critical t-value was calculated correctly
    def test_t_table(self):
        self.assertIn("n", globals())
        self.assertIn("t_table", globals())
        self.assertIsInstance(n, int)
        self.assertIsInstance(t_table, float)

        expected = float(t.ppf(1-(0.05/2), n-1))
        self.assertAlmostEqual(t_table, expected, places=5)

    # checks that the lower confidence interval bound was calculated correctly
    def test_lower_end(self):
        self.assertIn("x_bar", globals())
        self.assertIn("t_table", globals())
        self.assertIn("s", globals())
        self.assertIn("n", globals())
        self.assertIn("lower_end", globals())

        self.assertIsInstance(x_bar, float)
        self.assertIsInstance(t_table, float)
        self.assertIsInstance(s, float)
        self.assertIsInstance(n, int)
        self.assertIsInstance(lower_end, float)

        expected = x_bar - ((t_table * s) / math.sqrt(n))
        self.assertAlmostEqual(lower_end, expected, places=5)

    # checks that the upper confidence interval bound was calculated correctly
    def test_upper_end(self):
        self.assertIn("x_bar", globals())
        self.assertIn("t_table", globals())
        self.assertIn("s", globals())
        self.assertIn("n", globals())
        self.assertIn("upper_end", globals())

        self.assertIsInstance(x_bar, float)
        self.assertIsInstance(t_table, float)
        self.assertIsInstance(s, float)
        self.assertIsInstance(n, int)
        self.assertIsInstance(upper_end, float)

        expected = x_bar + ((t_table * s) / math.sqrt(n))
        self.assertAlmostEqual(upper_end, expected, places=5)

    # checks that the confidence interval question was answered with a boolean
    def test_answer_included(self):
        self.assertIn("answer_included", globals())
        self.assertIsInstance(answer_included, bool)

        expected = False
        self.assertEqual(answer_included, expected)

    # bonus: checks whether the correct value falls inside the confidence interval
    def test_bonus_answer_included(self):
        self.assertIn("answer_included", globals())
        self.assertIn("lower_end", globals())
        self.assertIn("right_answer", globals())
        self.assertIn("upper_end", globals())

        self.assertIsInstance(answer_included, bool)
        self.assertIsInstance(lower_end, float)
        self.assertIsInstance(right_answer, float)
        self.assertIsInstance(upper_end, float)

        expected = lower_end <= right_answer <= upper_end
        self.assertEqual(answer_included, expected)


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
    print(f"[Autograder] Mock upload called — using local case1.csv")
    return {"case1.csv": b""}

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