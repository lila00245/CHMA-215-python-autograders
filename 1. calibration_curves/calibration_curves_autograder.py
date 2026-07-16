# imports
import nbformat                                                             # notebook file parsing/editing
from nbclient import NotebookClient                                         # runs notebooks like jupyter
from nbclient.exceptions import CellExecutionError as CallExecutionError    # cell crash errors

import unittest                                                             # testing framework

import os                                                                   # file/folder handling
import csv                                                                  # output grade report
import re                                                                   # filename cleanup
import builtins                                                             # protects max/min if student overwrites them

# needed for calibration curves / graphs
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba


# ---------------- CONFIG ----------------
# folder containing all student submissions (.ipynb files)
SUBMISSIONS_FOLDER = "1. calibration_curves/submissions"

# final output file that stores all grades + feedback
OUTPUT_CSV = "1. calibration_curves/calibration_curves_grade_report.csv"

# expected value for tests
TITLE_KEYWORDS = ["calibration", "curve", "concentration", "response"]
XLABEL_KEYWORDS = ["concentration"]
YLABEL_KEYWORDS = ["detector", "response"]
BLACK = to_rgba("black")
RED = to_rgba("red")

# points per test
TEST_POINTS = {
    "test_corrected_response2": 1,
    "test_corrected_response4": 1,
    "test_corrected_responses": 2,
    "test_corrected_unk": 1,
    "test_x_array": 1,
    "test_y_array": 1,
    "test_points_color": 1,
    "test_trendline_color": 1,
    "test_plot_title": 1,
    "test_plot_xlabel": 1,
    "test_plot_ylabel": 1,
    "test_gridlines": 1,
    "test_x": 2
}

# human readable descriptions for students
TEST_DESCRIPTIONS = {
    "test_corrected_response2": "corrected_response2 value is incorrect",
    "test_corrected_response4": "corrected_response4 value is incorrect",
    "test_corrected_responses": "corrected_responses value(s) are incorrect",
    "test_corrected_unk": "corrected_unk value is incorrect",
    "test_x_array": "x_array values are incorrect",
    "test_y_array": "y_array values are incorrect",
    "test_points_color": "color of data points has not been changed",
    "test_trendline_color": "color of trendline has not been changed",
    "test_plot_title": "plot title missing required keywords",
    "test_plot_xlabel": "x-axis label missing required keywords",
    "test_plot_ylabel": "y-axis label missing required keywords",
    "test_gridlines": "gridlines have not been turned on",
    "test_x": "x value is incorrect"
}

# bonus points
BONUS_POINTS = {
    "test_bonus_linestyle": 0.25,
    "test_bonus_linewidth": 0.25,
    "test_bonus_gridline_customization": 0.25,
    "test_bonus_axis_limits": 0.25
}

# human readable descriptions for bonus tests
BONUS_DESCRIPTIONS = {
    "test_bonus_linestyle": "you changed the plot's linestyle",
    "test_bonus_linewidth": "you changed the plot's linewidth",
    "test_bonus_gridline_customization": "you customized the gridlines",
    "test_bonus_axis_limits": "you changed the x/y axis limits"
}


# -----------------------------------------
# used to find title and axes labels from plot
def get_last_axes():
    figs = list(map(plt.figure, plt.get_fignums()))
    if not figs:
        raise AssertionError("no figures found in the notebook.")
    if not figs[-1].axes:
        raise AssertionError("no axes found in the last figure.")
    return figs[-1].axes[0]

def reset_matplotlib_state():
    plt.close('all')    # clears all figures and axes


# ---------------- TEST CASES ----------------
class StudentTests(unittest.TestCase):
    '''
    checks if variable exists, 
    if it's the correct instance or type, 
    and if the value is correct
    '''

    # checks that corrected_response2 was calculated correctly.
    def test_corrected_response2(self):
        self.assertIn("response", globals())
        self.assertIn("corrected_response2", globals())
        self.assertIsInstance(response, list)
        self.assertIsInstance(corrected_response2, float)

        expected = response[2] - response[0]
        self.assertAlmostEqual(corrected_response2, expected, places=5)

    # checks that corrected_response4 was calculated correctly.
    def test_corrected_response4(self):
        self.assertIn("response", globals())
        self.assertIn("corrected_response4", globals())
        self.assertIsInstance(response, list)
        self.assertIsInstance(corrected_response4, float)

        expected = response[4] - response[0]
        self.assertAlmostEqual(corrected_response4, expected, places=5)

    # checks that the unknown response was corrected correctly.
    def test_corrected_unk(self):
        self.assertIn("response", globals())
        self.assertIn("unk", globals())
        self.assertIn("corrected_unk", globals())
        self.assertIsInstance(response, list)
        self.assertIsInstance(unk, float)
        self.assertIsInstance(corrected_unk, float)

        expected = unk - response[0]
        self.assertAlmostEqual(corrected_unk, expected, places=5)

    # checks that all corrected response values were added to the list correctly.
    def test_corrected_responses(self):
        self.assertIn("response", globals())
        self.assertIn("corrected_responses", globals())
        self.assertIsInstance(response, list)
        self.assertIsInstance(corrected_responses, list)

        expected = [value - response[0] for value in response]
        self.assertEqual(len(corrected_responses), len(expected))
        for i, val in enumerate(expected):
            self.assertAlmostEqual(corrected_responses[i], val, places=5)

    # checks that the x array was created correctly.
    def test_x_array(self):
        self.assertIn("conc", globals())
        self.assertIn("x_array", globals())
        self.assertIsInstance(conc, list)
        self.assertIsInstance(x_array, np.ndarray)

        expected = np.array(conc)
        np.testing.assert_array_equal(x_array, expected)

    # checks that the y array was created correctly.
    def test_y_array(self):
        self.assertIn("corrected_responses", globals())
        self.assertIn("y_array", globals())
        self.assertIsInstance(corrected_responses, list)
        self.assertIsInstance(y_array, np.ndarray)

        expected = np.array(corrected_responses)
        np.testing.assert_array_equal(y_array, expected)

    # checks that the scatter plot points are not black.
    def test_points_color(self):
        ax = get_last_axes()

        scatter = None
        for coll in ax.collections:
            if hasattr(coll, "get_facecolors"):
                scatter = coll
                break
        self.assertIsNotNone(scatter)

        actual_colors = scatter.get_facecolors()
        self.assertGreater(len(actual_colors), 0)
        for color in actual_colors:
            self.assertFalse(np.allclose(color, BLACK, atol=1e-8))

    # checks that the trendline color was changed from red.
    def test_trendline_color(self):
        ax = get_last_axes()
        lines = ax.get_lines()
        self.assertGreater(len(lines), 0)

        trendline = lines[-1]
        actual_color = to_rgba(trendline.get_color())
        self.assertFalse(np.allclose(actual_color, RED, atol=1e-8))

    # checks that the trendline style was customized.
    def test_bonus_linestyle(self):
        ax = get_last_axes()
        lines = ax.get_lines()
        self.assertTrue(lines)
        self.assertTrue(any(line.get_linestyle() != "-" for line in lines))

    # checks that the trendline width was customized.
    def test_bonus_linewidth(self):
        ax = get_last_axes()
        lines = ax.get_lines()
        self.assertTrue(lines)
        self.assertTrue(any(line.get_linewidth() != 1.5 for line in lines))

    # checks that the graph has an appropriate title.
    def test_plot_title(self):
        ax = get_last_axes()
        title = ax.get_title().lower()
        self.assertTrue(any(word in title for word in TITLE_KEYWORDS))

    # checks that the x-axis label was added correctly.
    def test_plot_xlabel(self):
        ax = get_last_axes()
        xlabel = ax.get_xlabel().lower()
        self.assertTrue(any(word in xlabel for word in XLABEL_KEYWORDS))

    # checks that the y-axis label was added correctly.
    def test_plot_ylabel(self):
        ax = get_last_axes()
        ylabel = ax.get_ylabel().lower()
        self.assertTrue(any(word in ylabel for word in YLABEL_KEYWORDS))

    # checks that gridlines are enabled.
    def test_gridlines(self):
        ax = get_last_axes()
        grid_on_x = any(line.get_visible() for line in ax.get_xgridlines())
        grid_on_y = any(line.get_visible() for line in ax.get_ygridlines())
        self.assertTrue(grid_on_x and grid_on_y)

    # checks that the gridlines were customized.
    def test_bonus_gridline_customization(self):
        ax = get_last_axes()
        gridlines = ax.get_xgridlines() + ax.get_ygridlines()

        customized = False
        for line in gridlines:
            if not line.get_visible():
                continue
            if (
                line.get_linestyle() != "-"
                or not np.isclose(line.get_linewidth(), 0.8, atol=1e-8)
                or (
                    line.get_alpha() is not None
                    and not np.isclose(line.get_alpha(), 1.0, atol=1e-8)
                )
            ):
                customized = True
                break
        self.assertTrue(customized)

    # checks that the axis limits were customized.
    def test_bonus_axis_limits(self):
        ax = get_last_axes()
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        default_x = np.allclose(xlim, (-1.25, 26.25), atol=1e-8)
        default_y = np.allclose(ylim, (-39.52392857142858, 830.0025), atol=1e-8)

        self.assertTrue(not default_x and not default_y)

    # checks that the unknown concentration was calculated correctly.
    def test_x(self):
        self.assertIn("corrected_unk", globals())
        self.assertIn("m", globals())
        self.assertIn("b", globals())
        self.assertIn("x", globals())
        self.assertIsInstance(corrected_unk, float)
        self.assertIsInstance(m, float)
        self.assertIsInstance(b, float)
        self.assertIsInstance(x, float)

        expected = (corrected_unk - b) / m
        self.assertAlmostEqual(x, expected, places=5)


# ---------------- EXECUTION ----------------
def execute_notebook(path):
    """
    runs a student notebook safely and extracts all variables created.

    this function:
    1. loads the notebook file
    2. patches plt.show() (so figure doesn't show up after each notebook is tested)
    3. executes notebook cells in order
    4. builds a namespace of all variables created by student code

    even if the notebook crashes:
    - execution continues safely
    - partial results are still collected
    """
    
    with open(path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # patch plt.show() so figure remains unavailable
    patch_code = """
import matplotlib
import matplotlib.pyplot as plt
def _safe_show(*args, **kwargs):
    print("[grader] ignoring plt.show() to preserve figures for grading.")
    return
plt.show = _safe_show
"""

    patch_cell = nbformat.v4.new_code_cell(patch_code)
    nb.cells.insert(0, patch_cell)

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

            reset_matplotlib_state()

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