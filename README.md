# TENOR: Efficient Document Labeling/Topic Modeling Tool to Exploratory Data Analysis

🔥
TENOR is a user interface for speeding up document labeling process and reducing the number of documents needed to be labeled. See the paper for details:
- Poursabzi-Sangdeh, Forough, et al. (2016). Alto: Active learning with topic overviews for speeding label induction and document labeling. ACL. https://aclanthology.org/P16-1110.pdf
- New Paper Coming soon!!!🔥🔥🔥


## References

If you find this tool helpful, you can cite the following paper:

```bibtex
@inproceedings{poursabzi2016alto,
  title={Alto: Active learning with topic overviews for speeding label induction and document labeling},
  author={Poursabzi-Sangdeh, Forough and Boyd-Graber, Jordan and Findlater, Leah and Seppi, Kevin},
  booktitle={Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  pages={1158--1169},
  year={2016}
}
```


## Getting Started

This tool's frontend code interface is adopted from [this repository](https://github.com/daniel-stephens/community_resilience). To run the app interface locally with the default Bills dataset, follow these steps:


```bash
git clone https://github.com/Pinafore/2023-document-annotation.git
cd 2023-document-annotation
pip install -r requirements.txt
```

## Setup

#### 1. Data Preprocessing
Preprocess the data for topic model training. The processed data will be saved to the specified --new_json_path directory
```
./01_data_process.sh
```

#### 2. Training Topic Models

You can obtain trained topic models in two ways:

1. If you're looking to get started quickly without training your own models, we've got you covered. Pre-trained models on the bills dataset, configured with 35 topics, are ready for use. You can download these models directly from [Google Drive](https://drive.google.com/drive/folders/1-k6YcC2KLp8iULGF5zmpAYlpk49dbX4W?usp=sharing)


After downloading, place the model files in the following directory of your local repository:
```
./flask_app/Topic_Models/trained_Models/
```

2. Train Your Own Models

For those who need customized topic models, we provide a convenient script to facilitate the training process:

```bash
./02_train_model.sh
```

This script will lead you through the steps necessary to train new models, which will then be saved to the location specified in the bash script argument `--save_trained_model_path`.

**Configuration Note:**
The application defaults to using 35 topics for model training. If your requirements differ, please follow these steps to ensure compatibility:

1. Execute the model training script with the number of topics set to your preference.
2. Once training is complete, adjust the code in `app.py` to align with your model's topic count. Specifically, change the value on line 128 to correspond with the number of topics in your newly trained model.


#### 3. Starting the Web Application

To launch the web application on your local machine, execute the provided shell script by running the following command in your terminal:

```bash
./03_run_app.sh
```

Upon successful execution of the script, the web application will be available. You can access it by opening your web browser and navigating to:

```
http://localhost:5001
```

If you wish to use a different port than the default `5001`, ensure that the `03_run_app.sh` script is configured accordingly before starting the application.



## Dataset Information

This app supports two datasets:

1. **20newsgroup**: A collection of newsgroup documents.
2. **congressional_bill_project_dataset**: A compilation of Congressional Bill documents.

For the Congressional Bill dataset, the app uses data from these sources:

- [Comparative Agendas Project](https://www.comparativeagendas.net/us)
- [Congressional Bills](http://www.congressionalbills.org)

The original Bills dataset uses numbers as labels. To correlate topics with labels, consult the [Codebook](https://comparativeagendas.s3.amazonaws.com/codebookfiles/Codebook_PAP_2019.pdf).

## Interface Demonstration

<p align="center">
  <img src="/results/images/list3.png" alt="List Interface" width="900" title="List Interface"/>
  <br>
  <em>The List Interface provides a streamlined overview of documents grouped by topics.</em>
</p>

<p align="center">
  <img src="/results/images/doc3.png" alt="Document Interface" width="900" title="Document Interface"/>
  <br>
  <em>The Document Interface offers an immersive reading experience, providing ranked relevant topics and automatic highlights of keywords in the document.</em>
</p>


## Acknowledgements

This project was built upon the work of the following repositories:
- [Contextualized Topic Models](https://github.com/MilaNLProc/contextualized-topic-models)
- [Tomotopy](https://github.com/bab2min/tomotopy)

We extend our gratitude to the authors of these original repositories for their valuable contributions and inspiration.

## License

This project is licensed under the [MIT License](LICENSE.md) - see the LICENSE file for details.

## Contact

For any additional questions or comments, please contact [zli12321@umd.edu].

Thank you for using or contributing to the Document Annotation NLP Tool!
