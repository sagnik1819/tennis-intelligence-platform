"""
Module 8: Machine Learning Engine - Player Clustering & Radar Trait Profiling
Uses Scikit-Learn KMeans clustering, vectorized NumPy trait scoring, and
vectorized Euclidean similarity without mutating shared concurrent state.
"""
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.cluster import KMeans

TRAIT_KEYS = (
    "consistency",
    "power_volume",
    "tournament_stamina",
    "rank_momentum",
    "efficiency",
)


class TennisMLEngine:
    """
    Computes explainable Machine Learning clusters, radar trait features,
    and similar-player recommendation vectors from genuine ranking and tournament data.
    Thread-safe & stateless across concurrent invocations.
    """

    def fit_and_profile(self, players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Takes raw list of players with {id, name, rank, points, movement, competitions_played}.
        Generates 5 radar traits, cluster tiers, and attaches O(1) similar-player IDs.
        """
        if not players:
            return []

        num_players = len(players)

        pts_arr = np.array([float(p.get("points") or 0) for p in players], dtype=np.float64)
        comps_arr = np.maximum(
            np.array([float(p.get("competitions_played") or 1) for p in players], dtype=np.float64),
            1.0,
        )
        mov_arr = np.array([float(p.get("movement") or 0) for p in players], dtype=np.float64)
        rank_arr = np.array([float(p.get("rank") or 999) for p in players], dtype=np.float64)
        eff_arr = pts_arr / comps_arr

        X = np.column_stack((pts_arr, comps_arr, mov_arr, eff_arr))

        # Fit KMeans in local variable for thread-safety across concurrent requests
        k = min(3, max(1, num_players))
        if k > 1:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)
        else:
            clusters = np.zeros(num_players, dtype=int)

        # Map cluster IDs to sports tier titles based on cluster mean points
        cluster_means = {}
        for c in set(clusters.tolist()):
            mask = clusters == c
            cluster_means[c] = float(np.mean(pts_arr[mask]))

        sorted_clusters = sorted(cluster_means.keys(), key=lambda c: cluster_means[c], reverse=True)
        tier_names = {
            sorted_clusters[0]: "Elite Grand Slam Tier",
            sorted_clusters[1] if len(sorted_clusters) > 1 else sorted_clusters[0]: "High-Yield Contender",
            sorted_clusters[2] if len(sorted_clusters) > 2 else sorted_clusters[0]: "Challenger Circuit",
        }

        # Vectorized Trait Scores (0 to 100 scale)
        max_pts = float(np.max(pts_arr)) if np.max(pts_arr) > 0 else 1.0
        max_comps = float(np.max(comps_arr)) if np.max(comps_arr) > 0 else 1.0
        raw_comps = np.array([float(p.get("competitions_played") or 0) for p in players], dtype=np.float64)
        eff_denom = max_pts / max(max_comps, 1.0)

        consistency_v = np.clip(
            (1.0 - (rank_arr / max(num_players, 1))) * 40.0
            + np.where(mov_arr >= 0, 25.0, 10.0)
            + 30.0,
            35.0,
            98.0,
        )
        power_v = np.clip((pts_arr / max_pts) * 95.0, 30.0, 99.0)
        stamina_v = np.clip((raw_comps / max_comps) * 92.0, 25.0, 96.0)
        momentum_v = np.clip(60.0 + (mov_arr * 12.0), 30.0, 95.0)
        efficiency_v = np.clip(((pts_arr / np.maximum(raw_comps, 1.0)) / eff_denom) * 90.0, 28.0, 97.0)

        trait_matrix = np.round(
            np.column_stack((consistency_v, power_v, stamina_v, momentum_v, efficiency_v)),
            1,
        )

        # Precompute top-3 similar competitor IDs in one vectorized pass (up to 1000 players)
        similar_ids_by_idx: Optional[List[List[str]]] = None
        if 1 < num_players <= 1000:
            diff = trait_matrix[:, None, :] - trait_matrix[None, :, :]
            dist_matrix = np.linalg.norm(diff, axis=2)
            np.fill_diagonal(dist_matrix, np.inf)
            top_n = min(3, num_players - 1)
            similar_ids_by_idx = []
            for idx in range(num_players):
                row = dist_matrix[idx]
                top_idx = np.argpartition(row, top_n - 1)[:top_n] if top_n < num_players else np.argsort(row)[:top_n]
                top_idx = top_idx[np.argsort(row[top_idx])]
                similar_ids_by_idx.append([players[int(i)]["competitor_id"] for i in top_idx])

        profiled_players = []
        for idx, p in enumerate(players):
            row_traits = trait_matrix[idx]
            traits = {
                "consistency": float(row_traits[0]),
                "power_volume": float(row_traits[1]),
                "tournament_stamina": float(row_traits[2]),
                "rank_momentum": float(row_traits[3]),
                "efficiency": float(row_traits[4]),
            }

            p_copy = dict(p)
            p_copy["traits"] = traits
            p_copy["cluster_tier"] = tier_names.get(int(clusters[idx]), "Tour Contender")
            if similar_ids_by_idx is not None:
                p_copy["_similar_ids"] = similar_ids_by_idx[idx]
            profiled_players.append(p_copy)

        return profiled_players

    def get_similar_players(
        self,
        target_id: str,
        profiled_players: List[Dict[str, Any]],
        top_n: int = 3,
        player_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Finds closest players using precomputed O(1) IDs or vectorized Euclidean distance."""
        target = player_lookup.get(target_id) if player_lookup else next(
            (p for p in profiled_players if p["competitor_id"] == target_id), None
        )
        if not target or not target.get("traits"):
            return []

        precomputed = target.get("_similar_ids")
        if precomputed and player_lookup:
            resolved = [player_lookup[cid] for cid in precomputed[:top_n] if cid in player_lookup]
            if len(resolved) == min(top_n, max(0, len(profiled_players) - 1)):
                return resolved

        candidates = [p for p in profiled_players if p["competitor_id"] != target_id and p.get("traits")]
        if not candidates:
            return []

        t_vec = np.array([target["traits"][k] for k in TRAIT_KEYS], dtype=np.float32)
        mat = np.array([[p["traits"][k] for k in TRAIT_KEYS] for p in candidates], dtype=np.float32)
        dists = np.linalg.norm(mat - t_vec, axis=1)

        k = min(top_n, len(candidates))
        top_idx = np.argpartition(dists, k - 1)[:k] if k < len(candidates) else np.arange(len(candidates))
        top_idx = top_idx[np.argsort(dists[top_idx])]
        return [candidates[int(i)] for i in top_idx]


# Singleton instance
ml_engine = TennisMLEngine()
