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
SUBMISSIONS_FOLDER = "grubbs_test/submissions"

# folder where dataset used by notebooks is stored
CURRENT_FOLDER = "grubbs_test"

# dataset file that gets injected into student notebooks before execution
INPUT_CSV = "grubbs.csv"

# final output file that stores all grades + feedback
OUTPUT_CSV = "grubbs_test/grubbs_test_grade_report.csv"

# expected value for tests
EXPECTED_DATA_LIST = [346.05, 360.48, 368.74, 309.86, 444.23, 377.13, 356.76, 321.55, 391.55, 374.58, 375.25, 370.33, 345.59, 371.09, 390.87, 305.41, 362.44, 383.93, 340.39, 359.94]

# points per test
TEST_POINTS = {
    "test_data_list": 1,
    "test_data_from_csv": 1,
    "test_average": 1,
    "test_sd": 1,
    "test_min": 1,
    "test_max": 1,
    "test_min_dist": 1,
    "test_max_dist": 1,
    "test_potential_outlier": 2,
    "test_x": 1,
    "test_x_bar": 1,
    "test_s": 1,
    "test_g_calc": 3,
    "test_sig_val": 1,
    "test_dof": 1,
    "test_t_table": 1,
    "test_numerator": 1,
    "test_denominator": 2,
    "test_g_table": 4,
    "test_updated_list": 1,
    "test_final_avg": 1,
    "test_final_sd": 1
}

# human readable descriptions for students
TEST_DESCRIPTIONS = {
    "test_data_list": "data_list values are incorrect",
    "test_data_from_csv": "data_from_csv values are incorrect",
    "test_average": "average value is incorrect",
    "test_sd": "standard deviation value is incorrect",
    "test_min": "minimum value is incorrect",
    "test_max": "maximum value is incorrect",
    "test_min_dist": "distance between minimum and average is incorrect",
    "test_max_dist": "distance between maximum and average is incorrect",
    "test_potential_outlier": "potential outlier value is incorrect",
    "test_x": "x value is incorrect",
    "test_x_bar": "x_bar (mean of x) value is incorrect",
    "test_s": "sample standard deviation (s) value is incorrect",
    "test_g_calc": "g_calc value is incorrect",
    "test_sig_val": "significance value is incorrect",
    "test_dof": "degrees of freedom value is incorrect",
    "test_t_table": "t_table value is incorrect",
    "test_numerator": "numerator value is incorrect",
    "test_denominator": "denominator value is incorrect",
    "test_g_table": "g_table value is incorrect",
    "test_updated_list": "updated list value is incorrect",
    "test_final_avg": "final average value is incorrect",
    "test_final_sd": "final standard deviation value is incorrect"
}

BONUS_POINTS = {}
BONUS_DESCRIPTIONS = {}


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

    # checks that the data list was created correctly.
    def test_data_list(self):
        self.assertIn("data_list", globals())
        self.assertIsInstance(data_list, list)
        self.assertEqual(data_list, EXPECTED_DATA_LIST)

    # checks that the csv data was read correctly.
    def test_data_from_csv(self):
        self.assertIn("data_from_csv", globals())
        self.assertIsInstance(data_from_csv, list)
        self.assertEqual(data_from_csv, EXPECTED_DATA_LIST)

    # checks that the average was calculated correctly.
    def test_average(self):
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

    # checks that the minimum value was found correctly.
    def test_min(self):
        self.assertIn("data_list", globals())
        self.assertIn("min_val", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(min_val, float)

        expected = builtins.min(data_list)
        self.assertAlmostEqual(min_val, expected, places=5)

    # checks that the maximum value was found correctly.
    def test_max(self):
        self.assertIn("data_list", globals())
        self.assertIn("max_val", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(max_val, float)

        expected = builtins.max(data_list)
        self.assertAlmostEqual(max_val, expected, places=5)

    # checks that the distance from the mean to the minimum was calculated correctly.
    def test_min_dist(self):
        self.assertIn("avg", globals())
        self.assertIn("min_val", globals())
        self.assertIn("min_dist", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(min_val, float)
        self.assertIsInstance(min_dist, float)

        expected = absolute(avg, min_val)
        self.assertAlmostEqual(min_dist, expected, places=5)

    # checks that the distance from the mean to the maximum was calculated correctly.
    def test_max_dist(self):
        self.assertIn("avg", globals())
        self.assertIn("max_val", globals())
        self.assertIn("max_dist", globals())
        self.assertIsInstance(avg, float)
        self.assertIsInstance(max_val, float)
        self.assertIsInstance(max_dist, float)

        expected = absolute(avg, max_val)
        self.assertAlmostEqual(max_dist, expected, places=5)

    # checks that the correct potential outlier was selected.
    def test_potential_outlier(self):
        self.assertIn("min_val", globals())
        self.assertIn("max_val", globals())
        self.assertIn("min_dist", globals())
        self.assertIn("max_dist", globals())
        self.assertIn("potential_outlier", globals())
        self.assertIsInstance(potential_outlier, float)

        expected = max_val if max_dist > min_dist else min_val
        self.assertAlmostEqual(potential_outlier, expected, places=5)

    # checks that x was assigned correctly.
    def test_x(self):
        self.assertIn("x", globals())
        self.assertIn("potential_outlier", globals())
        self.assertIsInstance(x, float)
        self.assertIsInstance(potential_outlier, float)

        expected = potential_outlier
        self.assertAlmostEqual(x, expected, places=5)

    # checks that x_bar was assigned correctly.
    def test_x_bar(self):
        self.assertIn("x_bar", globals())
        self.assertIn("avg", globals())
        self.assertIsInstance(x_bar, float)
        self.assertIsInstance(avg, float)

        expected = avg
        self.assertAlmostEqual(x_bar, expected, places=5)

    # checks that s was assigned correctly.
    def test_s(self):
        self.assertIn("s", globals())
        self.assertIn("sd", globals())
        self.assertIsInstance(s, float)
        self.assertIsInstance(sd, float)

        expected = sd
        self.assertAlmostEqual(s, expected, places=5)

    # checks that G_calc was calculated correctly.
    def test_g_calc(self):
        self.assertIn("x", globals())
        self.assertIn("x_bar", globals())
        self.assertIn("s", globals())
        self.assertIn("G_calc", globals())
        self.assertIsInstance(G_calc, float)

        expected = absolute(x, x_bar) / s
        self.assertAlmostEqual(G_calc, expected, places=5)

    # checks that the significance value was calculated correctly.
    def test_sig_val(self):
        self.assertIn("data_list", globals())
        self.assertIn("sig_val", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(sig_val, float)

        alpha = 0.05
        expected = alpha / len(data_list)
        self.assertAlmostEqual(sig_val, expected, places=5)

    # checks that the degrees of freedom were calculated correctly.
    def test_dof(self):
        self.assertIn("data_list", globals())
        self.assertIn("dof", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(dof, int)

        expected = len(data_list) - 2
        self.assertEqual(dof, expected)

    # checks that the t-table value was calculated correctly.
    def test_t_table(self):
        self.assertIn("sig_val", globals())
        self.assertIn("dof", globals())
        self.assertIn("t_table", globals())
        self.assertIsInstance(sig_val, float)
        self.assertIsInstance(dof, int)
        self.assertIsInstance(t_table, float)

        expected = float(t.ppf(1 - sig_val, df=dof))
        self.assertAlmostEqual(t_table, expected, places=5)

    # checks that the numerator was calculated correctly.
    def test_numerator(self):
        self.assertIn("data_list", globals())
        self.assertIn("t_table", globals())
        self.assertIn("numerator", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(t_table, float)
        self.assertIsInstance(numerator, float)

        expected = (len(data_list) - 1) * t_table
        self.assertAlmostEqual(numerator, expected, places=5)

    # checks that the denominator was calculated correctly.
    def test_denominator(self):
        self.assertIn("data_list", globals())
        self.assertIn("t_table", globals())
        self.assertIn("denominator", globals())
        self.assertIsInstance(data_list, list)
        self.assertIsInstance(t_table, float)
        self.assertIsInstance(denominator, float)

        n = len(data_list)
        expected = math.sqrt(n * (n - 2 + t_table**2))
        self.assertAlmostEqual(denominator, expected, places=5)

    # checks that G_table was calculated correctly.
    def test_g_table(self):
        self.assertIn("numerator", globals())
        self.assertIn("denominator", globals())
        self.assertIn("G_table", globals())
        self.assertIsInstance(numerator, float)
        self.assertIsInstance(denominator, float)
        self.assertIsInstance(G_table, float)

        expected = numerator / denominator
        self.assertAlmostEqual(G_table, expected, places=5)

    # checks that the updated list was created correctly.
    def test_updated_list(self):
        self.assertIn("updated_list", globals())
        self.assertIn("data_list", globals())
        self.assertIn("G_calc", globals())
        self.assertIn("G_table", globals())
        self.assertIn("potential_outlier", globals())
        self.assertIsInstance(updated_list, list)

        expected = data_list.copy()
        if G_calc >= G_table:
            expected.remove(potential_outlier)

        self.assertEqual(updated_list, expected)

    # checks that the final average was calculated correctly.
    def test_final_avg(self):
        self.assertIn("updated_list", globals())
        self.assertIn("final_avg", globals())
        self.assertIsInstance(updated_list, list)
        self.assertIsInstance(final_avg, float)

        expected = statistics.mean(updated_list)
        self.assertAlmostEqual(final_avg, expected, places=5)

    # checks that the final sample standard deviation was calculated correctly.
    def test_final_sd(self):
        self.assertIn("updated_list", globals())
        self.assertIn("final_sd", globals())
        self.assertIsInstance(updated_list, list)
        self.assertIsInstance(final_sd, float)

        expected = statistics.stdev(updated_list)
        self.assertAlmostEqual(final_sd, expected, places=5)


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
    print(f"[Autograder] Mock upload called — using local grubbs.csv")
    return {"grubbs.csv": b""}

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