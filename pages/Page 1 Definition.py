import streamlit as st
from ipywidgets import interact
import numpy as np
import plotly.graph_objects as go
from typing import Tuple
from plotly.subplots import make_subplots


class DummyClassifier:
    def __init__(
        self, pos_label_args: Tuple[float, float], neg_label_args: Tuple[float, float]
    ):
        self.pos_label_mean, self.pos_label_std = pos_label_args
        self.neg_label_mean, self.neg_label_std = neg_label_args

    def predict(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        assert X.ndim == 2
        m, n = X.shape
        np.random.seed(40)
        postives = (
            np.random.randn(y[y == 1].shape[0]) * self.pos_label_std
            + self.pos_label_mean
        )
        np.random.seed(40)
        negatives = (
            np.random.randn(y[y == 0].shape[0]) * self.neg_label_std
            + self.neg_label_mean
        )
        return np.concatenate([postives, negatives], axis=-1)


def plot1(
    probabilities: np.ndarray, labels: np.ndarray, threshold: float
) -> np.ndarray:
    confusion_matrix = [[0, 0], [0, 0]]
    for actual, predicted in zip(labels, (probabilities >= threshold).astype(np.uint8)):
        confusion_matrix[actual][predicted] += 1

    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(
        go.Histogram(x=probabilities[labels == 1], name="Positive Labels", nbinsx=100),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Histogram(x=probabilities[labels == 0], name="Negatives Labels", nbinsx=100),
        row=1,
        col=1,
    )
    fig["layout"]["xaxis"]["title"] = "Model Output Probabilities"
    fig["layout"]["yaxis"]["title"] = "Num Counts"
    # Add vertical line at the threshold
    fig.add_shape(
        type="line",
        x0=threshold,
        x1=threshold,
        y0=0,
        y1=len(labels) / 10,
        line=dict(color="lightgray", dash="dot"),
    )
    text = [["TN: ", "FP: "], ["FN: ", "TP: "]]
    for i in range(2):
        for j in range(2):
            text[i][j] += str(confusion_matrix[i][j])
    # Create the confusion matrix plot
    fig.add_trace(
        go.Heatmap(
            z=confusion_matrix,
            x=["Predicted negative", "Predicted positive"],
            y=["Actual negative", "Actual positive"],
            colorscale="gray",
            showscale=False,
            reversescale=True,
            text=text,
            hoverinfo="text",
            texttemplate="%{text}",
            textfont={"size": 20},
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        title_text=f"Histogram Plot and Confusion matrix for thershold = {threshold}",
        width=800,
        height=800,
    )
    st.plotly_chart(fig)
    return confusion_matrix


def make_tpr_fpr(
    probabilities: np.ndarray, labels: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Data for the AUC-ROC curve
    fpr = []
    tpr = []
    for t in range(11):
        t = t / 10
        confusion_matrix = [[0, 0], [0, 0]]
        for actual, predicted in zip(labels, (probabilities >= t).astype(np.uint8)):
            confusion_matrix[actual][predicted] += 1
        fn, tp = confusion_matrix[1]
        tn, fp = confusion_matrix[0]
        tpr.append(tp / (tp + fn + 1e-20))
        fpr.append(fp / (fp + tn + 1e-20))
    return np.array(tpr), np.array(fpr)


def plot2(
    probabilities: np.ndarray,
    labels: np.ndarray,
    tpr: np.ndarray,
    fpr: np.ndarray,
    threshold: float,
    area: bool = False,
) -> np.ndarray:
    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(
        go.Histogram(x=probabilities[labels == 1], name="Positive labels", nbinsx=100),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Histogram(x=probabilities[labels == 0], name="Negative labels", nbinsx=100),
        row=1,
        col=1,
    )
    fig["layout"]["xaxis"]["title"] = "Model Output Probabilities"
    fig["layout"]["yaxis"]["title"] = "Num Counts"
    # Add vertical line at the threshold
    fig.add_shape(
        type="line",
        x0=threshold,
        x1=threshold,
        y0=0,
        y1=len(labels) / 10,
        line=dict(color="lightgray", dash="dot"),
        name="threshold",
    )
    # Roc curve
    if area:
        fig.add_trace(
            go.Scatter(
                x=fpr, y=tpr, mode="lines", fill="tozeroy", name="AUC ROC Curve"
            ),
            row=2,
            col=1,
        )
    else:
        fig.add_trace(
            go.Scatter(x=fpr, y=tpr, mode="lines", name="ROC Curve"), row=2, col=1
        )

    n = len(tpr)
    rand_series = np.arange(n) / 10
    fig.add_trace(
        go.Scatter(
            x=rand_series,
            y=rand_series,
            mode="lines",
            name="Random Classifier",
            line=dict(color="gray", dash="dot"),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        title="Prob distribution and ROC curve",
        xaxis2=dict(title="FPR"),
        yaxis2=dict(title="TPR"),
        xaxis2_range=[0, 1],
        yaxis2_range=[0, 1],
        showlegend=True,
        height=800,
    )

    fig.add_annotation(
        x=fpr[int(threshold * 10)],
        y=tpr[int(threshold * 10)],
        ax=0,
        ay=-40,
        text=f"threshold={threshold}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        row=2,
        col=1,
    )
    st.plotly_chart(fig)


def main():
    st.write(
        """
    # What is AUC-ROC?

    Before we delve into the explanation of AUC-ROC, let's establish-
    the fundamentals of a classifier, its output, and methods to evaluate it.

    Now, imagine that you have constructed a classifier. Given an input $X$,
    the model learns a function $f(X)$ that maps $X$ to probabilities.
    These probabilities can indicate the likelihood of our positive event.
    """
    )

    st.image("assets/p1.png")

    st.write(
        """
        Mathematically, the model can be represented as $f(X) = P(y=1|X)$.
        To determine whether a given probability corresponds to
        a positive or negative label,
        we need to define a threshold that converts this
        probability into a label.
    """
    )

    st.latex(
        r"""
            \begin{equation}
                y = \begin{cases} 
                    1 & \text{if } f(X) \geq t \\
                    0 & \text{otherwise}
            \end{cases}
        \end{equation}"""
    )

    st.write(
        """
    Here, $t$ represents the threshold value.

    If this sounds complicated Let's Try an example below.
    """
    )

    st.write(
        """
        Let's make a classifier.
        This classifier will output some probability of input
        being positive label. This will range of 0-1.
        We will decide some threshold say 0.5.
        Any model output > 0.5 in this case will
        be our **predicted positive** and anything below
        that will be **predicted negative**.
        Similarly, we will have **actual positive** and **actual negative**.

        We can now plot a 2x2 matrix of these actual, predicted positives and negatives.

        The confusion matrix is a table that summarizes
        the performance of a classification model.
        It provides a comprehensive view of the predicted and
        actual class labels for a given dataset.
        The components of a confusion matrix are as follows:

        1. True Positive (TP): This represents the cases where
            the model correctly predicted the positive class
            (i.e., predicted positive and the actual class is positive).

        2. True Negative (TN): This represents the cases
        where the model correctly predicted the negative
        class (i.e., predicted negative and the actual class is negative).

        3. False Positive (FP): Also known as a Type I error,
        this represents the cases where the model predicted
        the positive class incorrectly
        (i.e., predicted positive while the actual class is negative).

        4. False Negative (FN): Also known as a Type II error,
        this represents the cases where the model predicted
        the negative class incorrectly
        (i.e., predicted negative while the actual class is positive).

        These components are typically arranged in a matrix format,
        hence the name "confusion matrix." The matrix is usually presented as follows:

        ```
                    Actual Negative     Actual Positive
        Predicted   | True Positive  |  False Positive  |
        Positive    |                |                  |
        -----------------------------------------------
        Predicted   | False Negative |  True Negative   |
        Negative    |                |                  |
        ```

        The values in each cell of the matrix represent
        the count or frequency of observations falling into
        those specific categories. By analyzing the confusion matrix,
        various evaluation metrics such as accuracy, precision, recall,
        and F1 score can be calculated to assess the performance of a
        classification model.
    """
    )
    m, n = 1000, 100
    some_rand_input = np.random.rand(m, n)
    labels = np.hstack(
        [
            np.ones(int(np.ceil(m / 2))).astype(np.uint8),
            np.zeros(m // 2).astype(np.uint8),
        ]
    )
    threshold = 0.5
    clf = DummyClassifier(pos_label_args=(0.6, 0.01), neg_label_args=(0.2, 0.01))
    probs = clf.predict(some_rand_input, y=labels)
    plot1(probs, labels, threshold)

    st.write(
        """
        ## Exercise 1

        Here's an activity for us to undertake.
        We will incrementally adjust the threshold and
        observe the resulting changes in the confusion matrix.
        Please pay attention to the following aspects:

        1. How does the confusion matrix change at a threshold of 0?
        2. What occurs to the confusion matrix as we increase the threshold? 
             Which component (TP/FP/TN/FN) shows an increase or decrease?
        3. What happens to the TPR and FPR at thresholds of 0 and 1?
        4. What is the pattern observed when comparing TPR and FPR as the threshold increases?
        5. Can you identify a threshold value that achieves a TPR 
        close to 1 and an FPR close to 0? While there may be several thresholds, 
        please provide the lowest one.

        Let's now define TPR and FPR:

        **TPR - True Positive Rate**
        The fraction of true positives out of the total actual positives (TP + FN).
        """
    )
    st.latex(r"TPR = \frac {TP} {TP + FN}")

    st.write(
        """
        **FPR - False Positive Rate**
        The fraction of false positives out of the total actual negatives (TN + FP).
    """
    )
    st.latex(r"FPR = \frac {FP} {TN + FP}")

    m, n = 1000, 100
    some_rand_input = np.random.rand(m, n)
    labels = np.hstack(
        [
            np.ones(int(np.ceil(m / 2))).astype(np.uint8),
            np.zeros(m // 2).astype(np.uint8),
        ]
    )
    clf = DummyClassifier(pos_label_args=(0.6, 0.01), neg_label_args=(0.2, 0.01))
    probs = clf.predict(some_rand_input, y=labels)

    # Create a slider input
    slider_value = st.slider(
        "Select a threshold", min_value=0.0, max_value=1.0, step=0.02, format="%.2f"
    )

    def f1(threshold=0):
        confusion_matrix = plot1(probs, labels, threshold)
        fn, tp = confusion_matrix[1]
        tn, fp = confusion_matrix[0]
        st.write(f"TPR: {tp / (tp + fn + 1e-20)}")
        st.write(f"FPR: {fp / (fp + tn + 1e-20)}")

    f1(slider_value)

    st.write(
        """
        ## Observations

        Please interact with the slider and record your responses. 
        In the cell below, we will discuss these questions. 
        However, I encourage you to try answering them yourself.

        1. What occurs to the confusion matrix at a threshold of 0?

        Response: At threshold = 0, *TN = 0* as all of the observations are marked as positive, 
        thus *FP = maximum*. So $TPR = FPR = 1$

        2. How does the confusion matrix change as we increase 
        the threshold? Which component (TP/FP/TN/FN) is increasing or decreasing?

        Response: As we increase the threshold, 
        FP decreases and TN increases, 
        after a point when threshold crosses the positive distribution, 
        the TP decreases and FN increases.
    """
    )
    st.image("assets/p2.png")

    st.write(
        """
        3. What happens to TPR and FPR at thresholds of 0 and 1?
             
        Response: At threshold = 0, TPR = FPR = 1, 
        since everything is predicted positive therefore tn = fn = 0.
        At threshold = 1, TPR = FPR = 0, since everything is predicted negative tp = fp = 0.

        4. What is the trend of TPR vs. FPR as the threshold increases?
             
        Response: First FPR decreases till we cross the negative distribution. 
        When we start to cross positive distribution, 
        tpr also start to decrease. Seems like there is an inverse relationship.
             
        5. Can you identify a threshold that yields 
        TPR close to 1 and FPR close to 0? 
        There may be multiple thresholds, but please provide the lowest one.

        Response: 0.24, at this point we have tpr = 1 and FPR = 0
    """
    )

    st.write(
        """
        # What is ROC curve and How to plot it?
        
        Now we have seen, how confusion matrix change as threshold changes. 
        This results in change in tpr and fpr. If we plot tpr vs fpr for 
        different thresholds then the curve we get is called ROC Curve.

        Below is a visualization that plots tpr and fpr for different thresholds.
    """
    )

    st.write(
        """
    Let's make some adjustments to the thresholds and perform the following
    observations:

    1. Initially, examine the threshold line in the predicted distribution.
    2. Next, observe the threshold arrow and note the corresponding
        TPR and FPR values for that particular threshold.

    Observe how for this case threshold arrow move right and then down.
    Till threshold = 0.5, tpr remains 1, but fpr decreases, after 0.5
    tpr and fpr both decreases.
    """
    )

    m, n = 1000, 100
    some_rand_input = np.random.rand(m, n)
    labels = np.hstack(
        [
            np.ones(int(np.ceil(m / 2))).astype(np.uint8),
            np.zeros(m // 2).astype(np.uint8),
        ]
    )
    clf = DummyClassifier(pos_label_args=(0.6, 0.01), neg_label_args=(0.2, 0.01))
    probs = clf.predict(some_rand_input, y=labels)

    tpr, fpr = make_tpr_fpr(probs, labels)

    def f2(threshold=0):
        plot2(probs, labels, tpr, fpr, threshold, area=True)

    slider_value1 = st.slider(
        "Select a threshold", min_value=0.0, max_value=1.0, step=0.1, format="%.1f"
    )
    f2(slider_value1)

    st.write(
        """
        The scenario we observed is an extremely ideal case
        where the classifier performs flawlessly. 
        It implies that there is a threshold value where 
        both the True Positive Rate (TPR) 
        and False Positive Rate (FPR) are equal to 1 and 0, respectively.
        If you manage to develop a classifier that achieves such performance,
        congratulations! However, in my experience,
        I have never come across a problem where this level of perfection is attainable.
    """
    )
    st.image("https://media.giphy.com/media/WeMey6bXiYmnEnKnvj/giphy.gif")

    st.write("This is how you plot a ROC curve.")
    st.write(
        """
    ### So what is AUC-ROC? you ask

    It is area under the roc curve. In the 2nd figure below, its the shaded green area.

    In this case it is a rectangle of l = 1, b = 1, thus area = l x b = 1

    Hence AUC ROC = 1. A perfect case
    """
    )


st.set_page_config(page_title="Auc Definition", page_icon="⭐️")

main()
