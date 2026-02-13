"""
Advanced Predictive Performance Model

Enhanced with:
- Age-based regression curves (player-specific aging)
- Peripheral stats (K%, BB%, Hard-Hit%, etc.)
- Multi-metric composite scoring
- Confidence intervals
- Contextual adjustments
"""
import pandas as pd
import numpy as np
from sqlalchemy import text
from src.utils.db_connection import get_session
from src.analytics.trend_tracker import TrendTracker
from src.analytics.regression_detector import RegressionDetector

class AdvancedPerformancePredictor:
    """
    Enhanced prediction model with aging curves and peripheral stats
    """
    
    def _to_float(self, value):
        """Convert Decimal or None to float"""
        if value is None:
            return None
        return float(value)
    
    def __init__(self):
        self.tracker = TrendTracker()
        self.detector = RegressionDetector()
        
        # MLB average aging curve (empirically derived)
        # Performance typically peaks at 27-28, then declines
        self.AGE_CURVE = {
            21: -8,   # Young, still developing
            22: -5,
            23: -3,
            24: -1,
            25: 0,
            26: 1,
            27: 2,    # Peak years
            28: 2,
            29: 1,
            30: 0,    # Start of decline
            31: -1,
            32: -2,
            33: -3,
            34: -5,
            35: -7,
            36: -10,
            37: -13,
            38: -16,
            39: -20,
            40: -25
        }
    
    def get_age_adjustment(self, current_age, next_age):
        """
        Calculate age-based adjustment using empirical aging curve
        
        Returns:
            Expected change in wRC+ due to aging
        """
        if not current_age or not next_age:
            return 0
        
        current_adj = self.AGE_CURVE.get(int(current_age), -25 if current_age > 40 else -8)
        next_adj = self.AGE_CURVE.get(int(next_age), -25 if next_age > 40 else -8)
        
        return next_adj - current_adj
    
    def calculate_plate_discipline_score(self, k_pct, bb_pct, career_k_pct, career_bb_pct):
        """
        Calculate plate discipline composite score
        
        Improving K% and BB% = positive signal
        Declining K% and BB% = negative signal
        
        Returns:
            Adjustment points and confidence
        """
        if not all([k_pct, bb_pct, career_k_pct, career_bb_pct]):
            return 0, 'NONE'
        
        # K% change (lower is better)
        k_delta = k_pct - career_k_pct
        
        # BB% change (higher is better)
        bb_delta = bb_pct - career_bb_pct
        
        # Score: Each 1% improvement in K% or BB% = ~2 wRC+ points
        k_score = -k_delta * 2  # Negative delta = improvement
        bb_score = bb_delta * 2  # Positive delta = improvement
        
        total_score = k_score + bb_score
        
        # Determine confidence
        if abs(k_delta) >= 3 or abs(bb_delta) >= 2:
            confidence = 'HIGH'
        elif abs(k_delta) >= 1.5 or abs(bb_delta) >= 1:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return round(total_score), confidence
    
    def calculate_power_sustainability_score(self, iso, hr_fb_pct, career_iso, career_hr_fb_pct):
        """
        Assess power sustainability using ISO and HR/FB%
        
        High HR/FB% relative to career = likely regression
        High ISO with normal HR/FB% = sustainable power
        
        Returns:
            Adjustment points and flags
        """
        if not all([iso, career_iso]):
            return 0, []
        
        iso_delta = iso - career_iso
        
        flags = []
        adjustment = 0
        
        # ISO change baseline
        if iso_delta > 0.060:
            flags.append('UNSUSTAINABLE_POWER_SPIKE')
            adjustment = -5
        elif iso_delta < -0.060:
            flags.append('POWER_DECLINE')
            adjustment = -3
        
        # HR/FB% check (if available)
        if hr_fb_pct and career_hr_fb_pct:
            hr_fb_delta = hr_fb_pct - career_hr_fb_pct
            
            if hr_fb_delta > 8:
                flags.append('INFLATED_HR_FB_PCT')
                adjustment -= 3
            elif hr_fb_delta < -8:
                flags.append('DEPRESSED_HR_FB_PCT')
                adjustment += 3
        
        return adjustment, flags
    
    def calculate_contact_quality_score(self, babip, career_babip, iso, career_iso):
        """
        Evaluate contact quality using BABIP and ISO together
        
        High BABIP + Low ISO = lucky singles hitter
        High BABIP + High ISO = legitimate power/speed combo
        Low BABIP + High ISO = unlucky power hitter
        
        Returns:
            Adjustment and interpretation
        """
        if not all([babip, career_babip, iso, career_iso]):
            return 0, 'UNKNOWN'
        
        babip_delta = babip - career_babip
        iso_delta = iso - career_iso
        
        # BABIP significantly above career
        if babip_delta > 0.040:
            if iso_delta < -0.030:
                # High BABIP but losing power = likely regression
                return -7, 'LUCKY_SINGLES'
            elif iso_delta > 0.030:
                # High BABIP with more power = legitimate improvement
                return +3, 'IMPROVED_CONTACT'
            else:
                # High BABIP, normal power = some luck
                return -4, 'BABIP_DRIVEN'
        
        # BABIP significantly below career
        elif babip_delta < -0.040:
            if iso_delta > 0.030:
                # Low BABIP but more power = bad luck
                return +7, 'UNLUCKY_POWER'
            else:
                # Low BABIP, normal power = bad luck
                return +5, 'UNLUCKY'
        
        return 0, 'NEUTRAL'
    
    def detect_skill_change(self, recent_seasons_df):
        """
        Detect genuine skill changes vs random variance
        
        Uses 3+ seasons to identify trends
        
        Returns:
            Dict with skill change indicators
        """
        if len(recent_seasons_df) < 3:
            return {'genuine_change': False}
        
        # Check for consistent trends across multiple metrics
        k_trend = np.polyfit(range(len(recent_seasons_df)), 
                            recent_seasons_df['k_pct'], 1)[0]
        bb_trend = np.polyfit(range(len(recent_seasons_df)), 
                             recent_seasons_df['bb_pct'], 1)[0]
        iso_trend = np.polyfit(range(len(recent_seasons_df)), 
                              recent_seasons_df['iso'], 1)[0]
        
        # Significant trends
        significant_k = abs(k_trend) > 1.5  # 1.5% K% change per year
        significant_bb = abs(bb_trend) > 0.8  # 0.8% BB% change per year
        significant_iso = abs(iso_trend) > 0.025  # 0.025 ISO change per year
        
        # Count significant trends
        num_significant = sum([significant_k, significant_bb, significant_iso])
        
        return {
            'genuine_change': num_significant >= 2,
            'k_trend': k_trend,
            'bb_trend': bb_trend,
            'iso_trend': iso_trend,
            'improving': (k_trend < -1 or bb_trend > 0.5 or iso_trend > 0.02),
            'declining': (k_trend > 1 or bb_trend < -0.5 or iso_trend < -0.02)
        }
    
    def predict_next_season_advanced(self, player_id, current_season=2025):
        """
        Advanced prediction with peripheral stats and aging curves
        
        Returns:
            Detailed prediction dict
        """
        session = get_session()
        
        try:
            # Get recent performance (3 years)
            query = text("""
                SELECT 
                    ss.season, ss.wrc_plus, ss.babip, ss.k_pct, ss.bb_pct, 
                    ss.iso, ss.hr_fb_pct, ss.pa,
                    CASE 
                        WHEN p.birth_date IS NOT NULL 
                        THEN ss.season - EXTRACT(YEAR FROM p.birth_date)
                        ELSE NULL 
                    END as age
                FROM season_stats ss
                JOIN players p ON ss.player_id = p.player_id
                WHERE ss.player_id = :player_id
                  AND ss.season <= :season
                  AND ss.pa >= 100
                ORDER BY ss.season DESC
                LIMIT 3
            """)
            
            recent = pd.read_sql(query, session.bind, 
                               params={'player_id': player_id, 'season': current_season})
            
            if recent.empty:
                return None
            
            # Get career baseline
            career_baseline = self.detector._get_player_career_baseline(player_id, current_season)
            
            if not career_baseline:
                return None
            
            # Calculate weighted baseline (more weight to recent)
            weights = np.array([0.5, 0.3, 0.2])[:len(recent)]
            weights = weights / weights.sum()
            
            baseline_wrc = (recent['wrc_plus'] * weights).sum()
            current_age = recent.iloc[0]['age']
            next_age = current_age + 1 if current_age else None
            
            # Component 1: Age Adjustment
            age_adj = self.get_age_adjustment(current_age, next_age)
            
            # Get latest season values
            latest = recent.iloc[0]
            
            # Convert to floats to avoid Decimal issues
            latest_k_pct = self._to_float(latest['k_pct'])
            latest_bb_pct = self._to_float(latest['bb_pct'])
            latest_iso = self._to_float(latest['iso'])
            latest_hr_fb_pct = self._to_float(latest['hr_fb_pct'])
            latest_babip = self._to_float(latest['babip'])
            
            career_k_pct = self._to_float(career_baseline['career_k_pct'])
            career_bb_pct = self._to_float(career_baseline['career_bb_pct'])
            career_iso = self._to_float(career_baseline['career_iso'])
            career_hr_fb_pct = self._to_float(career_baseline['career_hr_fb_pct'])
            career_babip = self._to_float(career_baseline['career_babip'])
            
            # Component 2: Plate Discipline
            discipline_adj, discipline_conf = self.calculate_plate_discipline_score(
                latest_k_pct, latest_bb_pct,
                career_k_pct, career_bb_pct
            )
            
            # Component 3: Power Sustainability
            power_adj, power_flags = self.calculate_power_sustainability_score(
                latest_iso, latest_hr_fb_pct,
                career_iso, career_hr_fb_pct
            )
            
            # Component 4: Contact Quality
            contact_adj, contact_type = self.calculate_contact_quality_score(
                latest_babip, career_babip,
                latest_iso, career_iso
            )
            
            # Component 5: Skill Change Detection
            skill_change = self.detect_skill_change(recent)
            
            skill_adj = 0
            if skill_change['genuine_change']:
                if skill_change['improving']:
                    skill_adj = +5
                elif skill_change['declining']:
                    skill_adj = -5
            
            # Component 6: Traditional Regression Signals
            regression_adj = 0
            latest_season = int(recent.iloc[0]['season'])
            regression_analysis = self.detector.analyze_player_season(player_id, latest_season)
            
            if regression_analysis and regression_analysis['alerts']:
                tier1_buys = len([a for a in regression_analysis['alerts'] 
                                 if a['tier'] == 1 and a['signal'] == 'BUY'])
                tier1_sells = len([a for a in regression_analysis['alerts'] 
                                  if a['tier'] == 1 and a['signal'] == 'SELL'])
                
                regression_adj = (tier1_buys * 4) - (tier1_sells * 4)
            
            # Calculate final prediction
            predicted_wrc = (
                baseline_wrc + 
                age_adj + 
                discipline_adj + 
                power_adj + 
                contact_adj + 
                skill_adj +
                regression_adj
            )
            
            # Calculate confidence
            total_pa = recent['pa'].sum()
            wrc_std = recent['wrc_plus'].std()
            age_certainty = current_age is not None
            
            if total_pa >= 1200 and wrc_std < 15 and age_certainty:
                confidence = 'HIGH'
            elif total_pa >= 600 and age_certainty:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'
            
            # Calculate prediction range (±1 standard deviation)
            prediction_std = max(wrc_std, 10)  # Minimum 10 point uncertainty
            lower_bound = predicted_wrc - prediction_std
            upper_bound = predicted_wrc + prediction_std
            
            return {
                'predicted_wrc': round(predicted_wrc),
                'prediction_range': (round(lower_bound), round(upper_bound)),
                'baseline_wrc': round(baseline_wrc),
                'current_age': int(current_age) if current_age else None,
                'next_age': int(next_age) if next_age else None,
                
                # Component adjustments
                'age_adjustment': round(age_adj),
                'discipline_adjustment': discipline_adj,
                'power_adjustment': power_adj,
                'contact_adjustment': contact_adj,
                'skill_change_adjustment': skill_adj,
                'regression_adjustment': regression_adj,
                
                # Flags and metadata
                'power_flags': power_flags,
                'contact_type': contact_type,
                'skill_change': skill_change,
                'discipline_confidence': discipline_conf,
                'confidence': confidence,
                'sample_size_pa': int(total_pa),
                'recent_seasons': len(recent)
            }
        
        finally:
            session.close()
    
    def generate_prediction_report(self, player_name, current_season=2025):
        """
        Generate detailed prediction report for a player
        """
        session = get_session()
        
        try:
            result = session.execute(
                text("SELECT player_id FROM players WHERE name = :name"),
                {'name': player_name}
            ).fetchone()
            
            if not result:
                return f"Player '{player_name}' not found"
            
            player_id = result[0]
            pred = self.predict_next_season_advanced(player_id, current_season)
            
            if not pred:
                return f"Insufficient data for {player_name}"
            
            # Build report
            report = []
            report.append("=" * 70)
            report.append(f"ADVANCED PREDICTION: {player_name} ({current_season + 1})")
            report.append("=" * 70)
            
            report.append(f"\n📊 PREDICTION:")
            report.append(f"   Projected wRC+: {pred['predicted_wrc']}")
            report.append(f"   Range (±1σ): {pred['prediction_range'][0]}-{pred['prediction_range'][1]}")
            report.append(f"   Baseline (3-yr): {pred['baseline_wrc']}")
            report.append(f"   Confidence: {pred['confidence']}")
            
            report.append(f"\n👤 AGE PROFILE:")
            report.append(f"   Current Age: {pred['current_age']}")
            report.append(f"   Next Season Age: {pred['next_age']}")
            report.append(f"   Age Adjustment: {pred['age_adjustment']:+d} wRC+")
            
            report.append(f"\n🎯 COMPONENT BREAKDOWN:")
            report.append(f"   Plate Discipline: {pred['discipline_adjustment']:+d} wRC+ ({pred['discipline_confidence']} confidence)")
            report.append(f"   Power Sustainability: {pred['power_adjustment']:+d} wRC+")
            report.append(f"   Contact Quality: {pred['contact_adjustment']:+d} wRC+ ({pred['contact_type']})")
            report.append(f"   Skill Change: {pred['skill_change_adjustment']:+d} wRC+")
            report.append(f"   Regression Signals: {pred['regression_adjustment']:+d} wRC+")
            
            if pred['power_flags']:
                report.append(f"\n⚠️  POWER FLAGS:")
                for flag in pred['power_flags']:
                    report.append(f"   - {flag}")
            
            if pred['skill_change']['genuine_change']:
                report.append(f"\n📈 SKILL CHANGE DETECTED:")
                sc = pred['skill_change']
                report.append(f"   K% Trend: {sc['k_trend']:.2f}% per year")
                report.append(f"   BB% Trend: {sc['bb_trend']:.2f}% per year")
                report.append(f"   ISO Trend: {sc['iso_trend']:.3f} per year")
                trend_dir = "Improving" if sc['improving'] else "Declining" if sc['declining'] else "Stable"
                report.append(f"   Overall: {trend_dir}")
            
            report.append(f"\n📊 SAMPLE:")
            report.append(f"   Total PA (3yr): {pred['sample_size_pa']}")
            report.append(f"   Seasons: {pred['recent_seasons']}")
            
            report.append("\n" + "=" * 70)
            
            return "\n".join(report)
        
        finally:
            session.close()


if __name__ == "__main__":
    print("=" * 70)
    print("ADVANCED PREDICTIVE MODEL WITH AGING CURVES")
    print("=" * 70)
    
    predictor = AdvancedPerformancePredictor()
    
    # Test players at different career stages
    test_players = [
        "Harrison Bader",
        "Aaron Judge",
        "Shohei Ohtani",
        "Paul Goldschmidt",  # Older player
        "Bobby Witt Jr.",     # Young player
    ]
    
    for player in test_players:
        print(f"\n{predictor.generate_prediction_report(player, 2025)}\n")