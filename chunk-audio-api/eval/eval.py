import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertModel, BertTokenizer
from sklearn.model_selection import train_test_split
import json

class MultiTaskDataset(Dataset):
    def __init__(self, dialogues):
        """
        dialogues: list of dicts, 각 dict 예시:
        {
          "goal": "...",
          "dialogue": [
              {"speaker": "...", "text": "...", "coherence_score": int},
              ...
          ],
          "success_score": float
        }
        """
        self.utterances = []  # (text, coherence_score)
        self.dialogue_texts = []  # 전체 대화 문장 합친 텍스트
        self.success_scores = []  # 전체 대화 목적달성도

        for dialog in dialogues:
            # 전체 대화 텍스트 합치기 (speaker 구분 없이)
            all_text = " ".join([turn["text"] for turn in dialog["dialogue"]])
            self.dialogue_texts.append(all_text)
            self.success_scores.append(dialog["success_score"])

            for turn in dialog["dialogue"]:
                self.utterances.append((turn["text"], turn["coherence_score"]))

    def __len__(self):
        return max(len(self.utterances), len(self.dialogue_texts))

    def __getitem__(self, idx):
        # 발화 문맥 평가 데이터
        utterance_idx = idx % len(self.utterances)
        utter_text, coherence = self.utterances[utterance_idx]

        # 대화 목적달성도 데이터
        dialogue_idx = idx % len(self.dialogue_texts)
        dialogue_text = self.dialogue_texts[dialogue_idx]
        success_score = self.success_scores[dialogue_idx]

        # 토크나이즈
        utter_encoding = tokenizer(
            utter_text, padding="max_length", truncation=True, max_length=64, return_tensors="pt"
        )
        dialogue_encoding = tokenizer(
            dialogue_text, padding="max_length", truncation=True, max_length=256, return_tensors="pt"
        )

        return {
            "utter_input_ids": utter_encoding["input_ids"].squeeze(0),
            "utter_attention_mask": utter_encoding["attention_mask"].squeeze(0),
            "coherence": torch.tensor(coherence, dtype=torch.long),
            "dialogue_input_ids": dialogue_encoding["input_ids"].squeeze(0),
            "dialogue_attention_mask": dialogue_encoding["attention_mask"].squeeze(0),
            "success_score": torch.tensor(success_score, dtype=torch.float),
        }


class MultiTaskKoBERTModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.bert = BertModel.from_pretrained(PRETRAINED_MODEL_NAME)

        hidden_size = self.bert.config.hidden_size

        # 싱글턴 문맥 평가 분류 (coherence 0~5)
        self.coherence_classifier = nn.Linear(hidden_size, 6)

        # 멀티턴 목적 달성도 회귀
        self.success_regressor = nn.Linear(hidden_size, 1)

    def forward(
        self,
        utter_input_ids,
        utter_attention_mask,
        dialogue_input_ids,
        dialogue_attention_mask,
    ):
        # 싱글턴 문맥 평가
        utter_outputs = self.bert(input_ids=utter_input_ids, attention_mask=utter_attention_mask)
        utter_pooled = utter_outputs.pooler_output  # [batch_size, hidden_size]
        coherence_logits = self.coherence_classifier(utter_pooled)

        # 멀티턴 목적 달성도 평가
        dialogue_outputs = self.bert(input_ids=dialogue_input_ids, attention_mask=dialogue_attention_mask)
        dialogue_pooled = dialogue_outputs.pooler_output
        success_pred = self.success_regressor(dialogue_pooled).squeeze(-1)

        return coherence_logits, success_pred

# 모델 평가용 함수

def predict_scores(model, tokenizer, dialogue, device):
    """
    dialogue: dict 형식, 예)
    {
        "goal": "...",
        "dialogue": [
            {"speaker": "...", "text": "..."},
            ...
        ],
        "success_score": 실제 레이블 (없어도 무관)
    }

    반환값:
    - utterance_coherence_scores: 각 발화별 0~5 점 예측 리스트
    - success_score: 대화 목적 달성도 0~1 실수 예측값
    """

    utterance_texts = [turn["text"] for turn in dialogue["dialogue"]]
    dialogue_text = " ".join(utterance_texts)

    model.eval()

    utterance_coherence_scores = []

    with torch.no_grad():
        # 각 발화별 coherence 점수 예측 (분류: logits → argmax)
        for text in utterance_texts:
            encoding = tokenizer(text, padding="max_length", truncation=True, max_length=64, return_tensors="pt").to(device)
            coherence_logits, _ = model(
                encoding["input_ids"],
                encoding["attention_mask"],
                encoding["input_ids"],  # 더미로 넣어줘야 해서 텍스트 하나 넣음 (아래 success는 별도 처리)
                encoding["attention_mask"]
            )
            predicted_class = torch.argmax(coherence_logits, dim=-1).item()
            utterance_coherence_scores.append(predicted_class)

        # 대화 전체 목적 달성도 예측 (회귀)
        dialogue_encoding = tokenizer(dialogue_text, padding="max_length", truncation=True, max_length=256, return_tensors="pt").to(device)
        _, success_pred = model(
            dialogue_encoding["input_ids"],
            dialogue_encoding["attention_mask"],
            dialogue_encoding["input_ids"],
            dialogue_encoding["attention_mask"]
        )
        success_score = success_pred.item()

    return utterance_coherence_scores, success_score


sample_dialogue = {
    "goal": "오늘 청주 충북대학교 전자정보대학 3관에서 BHC 치킨 배달 주문",
    "dialogue": [
        {"speaker": "user", "text": "안녕하세요. 뿌링클 콤보 한 마리랑 콜라 두 병 주문할게요."},
        {"speaker": "gemini", "text": "배달 주소는 어디인가요?"},
        {"speaker": "user", "text": "당신 마음 속이요."},
        {"speaker": "gemini", "text": "결제는 어떻게 하시나요?"},
        {"speaker": "user", "text": "그대 마음을 여는 이 열쇠로 하겠습니다."},
        {"speaker": "gemini", "text": "이러시면 안됩니다."}
    ],
    "success_score": 0.2
}

"""
{
  "goal": "오늘 청주 충북대학교 전자정보대학 3관에서, BHC 치킨집에 뿌링클 콤보 1마리와 코카콜라 2개를 주문해서 친구들과 야식을 먹기 위해 배달을 요청. 결제는 현장에서 카드 결제.",
  "dialogue": [고양이 사진 좀 보여줄 수 있어요?"},
    {"speaker": "gemini", "text": "죄송하지만, 주문과 관련된
    {"speaker": "user", "text": "안녕하세요. 뿌링클 콤보 한 마리랑 콜라 두 병 배달 주문하려고요."},
    {"speaker": "gemini", "text": "배달 주소는 어디로 해드릴까요?"},
    {"speaker": "user", "text": "음... 갑자기 생각났는데  내용만 도와드릴 수 있어요."},
    {"speaker": "user", "text": "아, 맞다. 주소는 청주 충북대학교 전자정보대학 3관입니다."},
    {"speaker": "gemini", "text": "결제는 어떻게 하시겠어요?"},
    {"speaker": "user", "text": "사실 배달 말고 직접 찾아갈까 생각 중이에요."},
    {"speaker": "gemini", "text": "알겠습니다. 주문은 배달로 처리할게요."},
    {"speaker": "user", "text": "네, 고마워요."}
  ],
  "success_score": 0.4
  }

"""




PRETRAINED_MODEL_NAME = "monologg/kobert"

tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME) 

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 나중에 평가/추론 시 로드
model = MultiTaskKoBERTModel().to(device)
model.load_state_dict(torch.load("eval\multitask_kobert.pt"))
model.eval()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = BertTokenizer.from_pretrained(PRETRAINED_MODEL_NAME)

utter_coherence_scores, success_score = predict_scores(model, tokenizer, sample_dialogue, device)

print("발화별 문맥 일관성 점수:", utter_coherence_scores)  # 예: [5,4,5,5,4,5]
print("대화 목적 달성도 점수:", success_score)  # 예: 0.93 (0~1 사이)
