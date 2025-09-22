import jiwer

def evaluate_accuracy(prediction: str, ground_truth: str):
    cer = jiwer.cer(ground_truth, prediction)
    wer = jiwer.wer(ground_truth, prediction)
    return round(cer, 4), round(wer, 4)
