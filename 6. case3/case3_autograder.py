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
SUBMISSIONS_FOLDER = "6. case3/submissions"

# folder where dataset used by notebooks is stored
CURRENT_FOLDER = "6. case3"

# dataset file that gets injected into student notebooks before execution
INPUT_CSV = "case3.csv"

# final output file that stores all grades + feedback
OUTPUT_CSV = "6. case3/case3_grade_report.csv"

# this is the correct dataset students are supposed to load
# used to verify they loaded and processed data correctly
EXPECTED_DATA_LIST1 = [37.7, 36.3, 37.0, 36.9, 36.8, 36.6, 36.9, 37.3, 36.5, 36.7, 36.5, 37.3, 36.5, 37.4, 37.8, 37.0, 37.0, 37.0, 37.3, 36.5]
EXPECTED_DATA_LIST2 = [37.6, 37.4, 36.8, 37.4, 37.4, 37.5, 37.3, 37.3, 37.6, 37.4, 37.3, 37.1, 37.1, 37.4, 37.3, 37.1, 37.1, 37.4, 37.2, 37.3]

# points per test
TEST_POINTS = {
    "test_data_list1": 1,
    "test_data_list2": 1,
    "test_differences_list": 2,
    "test_avg": 1,
    "test_sd": 1,
    "test_n": 1,
    "test_t_calc": 2,
    "test_t_table": 1,
    "test_statistically_different": 2
}

# human readable descriptions for students
TEST_DESCRIPTIONS = {
    "test_data_list1": "data_list1 values are incorrect",
    "test_data_list2": "data_list2 values are incorrect",
    "test_differences_list": "differences_list values are incorrect",
    "test_avg": "avg value is incorrect",
    "test_sd": "sd value is incorrect",
    "test_n": "n value is incorrect",
    "test_t_calc": "t_calc value is incorrect",
    "test_t_table": "t_table value is incorrect",
    "test_statistically_different": "statistically_different value is incorrect"
}

BONUS_POINTS = {
}

# feedback for what they got correct / bonus points for
BONUS_DESCRIPTIONS = {
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

    # checks that the first data list was created correctly.
    def test_data_list1(self):
        self.assertIn("data_list1", globals())
        self.assertIsInstance(data_list1, list)
        self.assertEqual(data_list1, EXPECTED_DATA_LIST1)

    # checks that the second data list was created correctly.
    def test_data_list2(self):
        self.assertIn("data_list2", globals())
        self.assertIsInstance(data_list2, list)
        self.assertEqual(data_list2, EXPECTED_DATA_LIST2)

    # checks that the difference list was created correctly.
    def test_differences_list(self):
        self.assertIn("differences_list", globals())
        self.assertIn("data_list1", globals())
        self.assertIn("data_list2", globals())
        self.assertIsInstance(differences_list, list)
        self.assertIsInstance(data_list1, list)
        self.assertIsInstance(data_list2, list)
        self.assertGreater(len(differences_list), 0)
        
        expected1 = [data_list1[i] - data_list2[i] for i in range(len(data_list1))]
        expected2 = [data_list2[i] - data_list1[i] for i in range(len(data_list1))]
        self.assertTrue(differences_list == expected1 or differences_list == expected2)

    # checks that the average was calculated correctly.
    def test_avg(self):
        self.assertIn("avg", globals())
        self.assertIn("differences_list", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(differences_list, list)

        expected = statistics.mean(differences_list)
        self.assertAlmostEqual(avg, expected, places=5)

    # checks that the sample standard deviation was calculated correctly.
    def test_sd(self):
        self.assertIn("sd", globals())
        self.assertIn("differences_list", globals())
        self.assertIsInstance(sd, float)
        self.assertIsInstance(differences_list, list)

        expected = statistics.stdev(differences_list)
        self.assertAlmostEqual(sd, expected, places=5)

    # checks that n was calculated correctly.
    def test_n(self):
        self.assertIn("n", globals())
        self.assertIn("differences_list", globals())
        self.assertIsInstance(n, int)
        self.assertIsInstance(differences_list, list)

        expected = len(differences_list)
        self.assertEqual(n, expected)

    # checks that t_calc was calculated correctly.
    def test_t_calc(self):
        self.assertIn("t_calc", globals())
        self.assertIn("avg", globals())
        self.assertIn("sd", globals())
        self.assertIn("n", globals())
        self.assertIsInstance(t_calc, float)
        self.assertIsInstance(avg, float)
        self.assertIsInstance(sd, float)
        self.assertIsInstance(n, int)

        expected = abs(avg) * math.sqrt(n) / sd
        self.assertAlmostEqual(t_calc, expected, places=5)

    # checks that t_table was calculated correctly.
    def test_t_table(self):
        self.assertIn("t_table", globals())
        self.assertIn("n", globals())
        self.assertIsInstance(t_table, float)
        self.assertIsInstance(n, int)

        expected = t_inv_2t(0.05, n-1)
        self.assertAlmostEqual(t_table, expected, places=5)

    # checks that the statistical comparison was performed correctly.
    def test_statistically_different(self):
        self.assertIn("statistically_different", globals())
        self.assertIn("t_calc", globals())
        self.assertIn("t_table", globals())
        self.assertIsInstance(statistically_different, bool)
        self.assertIsInstance(t_calc, float)
        self.assertIsInstance(t_table, float)

        expected = t_calc > t_table
        self.assertEqual(statistically_different, expected)


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
    print(f"[Autograder] Mock upload called — using local case3.csv")
    return {"case3.csv": b""}

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