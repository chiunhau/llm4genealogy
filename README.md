#  LLM for Genealogy
This repo contains the source code used for synthesizing data and evaluating the performance of LLMs in genealogy tasks. The main report can be found in `report.pdf`.


## Project Overview
Our goal is to test the ability of state-of-the-art LLMs in understanding and interpreting traditional Chinese genealogical images and explore how they can be used in digital humanities. 
We developed a program that generates synthetic genealogical images mimicking authentic Chinese genealogical images, and asked LLMs to answer two types of questions: 1) predict given two figures’ relationship in the family, and 2) identify all figures of a certain relationship of a given figure’s name. We generated a total of 60 genealogical images of various dimensions, and tested 22 questions against each image using Gemini 2.5 Flash and Gemini 3 Flash.

## Setup
- Please make sure you have Python 3 installed.
- Please make sure you have the required packages installed. You can install them using `pip install -r requirements.txt`.
- Please add your own `VERCEL_AI_GATEWAY_KEY` to the `.env` file.

### Data Synthesis
- `generate_trees.py` is the script used to generate the family trees. It outputs the family trees in the `data/family_trees_json` directory.
- A seperate web app, which is not included in the repo, is used to render the family trees from JSON into PNGs. You can find the rendered family trees in the `data/family_trees_images` directory. We will release the web app later.


### Test Cases Generation
- `generate_test_cases.py` is the script used to generate the test cases. It outputs the test cases in the `data/test_cases` directory.
- The test cases are generated based on the family trees in the `data/family_trees_json` directory.
- The test cases are stored in the `test_cases` directory 

### Test Execution
- Run `run_test_case_1.py` and `run_test_case_2.py` to run the test cases.
- The test results are stored in the `test_results` directory.
- Beware of the incurring LLM cost of running these scripts if you want to try yourself.

### Evaluation
- Run `evaluate_results_1.py` and `evaluate_results_2.py` to evaluate the results.
- Remember to change the `results_dir` in the scripts to the directory where your test results are stored.
- The evaluation results will be printed to the console.
