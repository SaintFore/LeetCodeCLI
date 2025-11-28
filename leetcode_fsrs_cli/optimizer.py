"""
FSRS 参数优化器
基于 Scipy 实现轻量级参数优化
"""

import math
import json
from typing import List, Dict, Tuple
from datetime import datetime

try:
    import numpy as np
    from scipy.optimize import minimize
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from .fsrs import FSRS

class FSRSOptimizer:
    """FSRS 参数优化器"""

    def __init__(self, fsrs: FSRS):
        self.fsrs = fsrs

    def optimize(self, reviews: List[Dict]) -> Tuple[List[float], float]:
        """
        优化 FSRS 参数
        
        Args:
            reviews: 复习记录列表 (扁平化)
            
        Returns:
            Tuple[List[float], float]: (优化后的权重, 最小Loss)
        """
        if not HAS_SCIPY:
            raise ImportError("需要安装 scipy 和 numpy 才能使用优化功能: pip install scipy numpy")

        if not reviews:
            raise ValueError("没有足够的复习记录进行优化")

        # 准备数据
        # 按题目分组并按时间排序
        reviews_by_qid = {}
        for r in reviews:
            qid = r["question_id"]
            if qid not in reviews_by_qid:
                reviews_by_qid[qid] = []
            reviews_by_qid[qid].append(r)

        for qid in reviews_by_qid:
            reviews_by_qid[qid].sort(key=lambda x: x["timestamp"])

        # 初始参数
        initial_w = np.array(self.fsrs.params["w"])
        
        # 定义边界 (参考 FSRS 实现)
        bounds = [
            (0.1, 10), (0.1, 10), (0.1, 10), (0.1, 10),
            (0.1, 10), (0.1, 10), (0.1, 10), (0.01, 10),
            (0.1, 10), (0.1, 10), (0.1, 10), (0.1, 10),
            (0.01, 10), (0.1, 10), (0.1, 10), (0.1, 10),
            (0.1, 10)
        ]

        # 运行优化
        result = minimize(
            self._loss_function,
            initial_w,
            args=(reviews_by_qid,),
            bounds=bounds,
            method='L-BFGS-B',
            options={'maxiter': 1000}
        )

        return result.x.tolist(), result.fun

    def _loss_function(self, w: np.ndarray, reviews_by_qid: Dict[int, List[Dict]]) -> float:
        """计算损失函数 (Log Loss)"""
        total_loss = 0
        total_count = 0
        
        # 临时更新 FSRS 参数
        original_w = self.fsrs.params["w"]
        self.fsrs.params["w"] = w.tolist()

        for qid, question_reviews in reviews_by_qid.items():
            # 初始状态
            stability = 2.5  # 这里的初始值应该由参数决定，但简化处理
            difficulty = 5.0
            
            # 第一条记录通常是学习，不计算 Loss，只更新状态
            # 但 FSRS v4 中第一条记录也有评分
            
            # 我们需要模拟整个过程
            # 初始: stability=w[0-3] based on first rating
            
            first_rating = question_reviews[0]["rating"]
            # 初始稳定性
            stability = w[first_rating - 1]
            # 初始难度
            difficulty = w[4] - w[5] * (first_rating - 3)
            difficulty = max(1, min(10, difficulty))
            
            last_date = datetime.fromisoformat(question_reviews[0]["timestamp"])

            for i in range(1, len(question_reviews)):
                review = question_reviews[i]
                current_date = datetime.fromisoformat(review["timestamp"])
                rating = review["rating"]
                
                elapsed_days = (current_date - last_date).total_seconds() / 86400
                elapsed_days = max(0, elapsed_days)

                # 计算留存率 (预测)
                retrievability = math.pow(1 + elapsed_days / (9 * stability), -1)
                
                # 计算 Loss
                # 评分映射: 1=忘记(y=0), 2-5=记住(y=1)
                y = 0 if rating == 1 else 1
                
                # 避免 log(0)
                p = max(1e-10, min(1 - 1e-10, retrievability))
                
                loss = - (y * math.log(p) + (1 - y) * math.log(1 - p))
                
                # 加权 (可选，这里简化)
                total_loss += loss
                total_count += 1

                # 更新状态
                if rating == 1:
                    new_difficulty = difficulty + w[15]
                    new_difficulty = max(1, min(10, new_difficulty))
                    stability = w[16] * math.pow(difficulty, w[17]) * math.pow(new_difficulty, -w[18])
                    difficulty = new_difficulty
                else:
                    # 难度更新
                    new_difficulty = difficulty + w[7] * (rating - 3)
                    new_difficulty = max(1, min(10, new_difficulty))
                    
                    # 稳定性更新
                    if rating == 2:
                        stability = w[9] * math.pow(difficulty, w[10]) * math.pow(new_difficulty, -w[11]) * stability
                    elif rating == 3:
                        stability = w[12] * math.pow(difficulty, w[13]) * math.pow(new_difficulty, -w[14]) * stability
                    else: # 4 or 5
                        stability = stability * (1 + w[5] * (5 - rating) * math.pow(retrievability, w[6]))
                    
                    difficulty = new_difficulty
                
                last_date = current_date

        # 恢复参数
        self.fsrs.params["w"] = original_w
        
        return total_loss / total_count if total_count > 0 else 0
