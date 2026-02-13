"""
Alert Digest Generator

Creates clean, actionable reports from daily scraper results
"""
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class AlertDigest:
    """
    Generate clean alert reports
    """
    
    def __init__(self, results_file=None):
        if results_file:
            with open(results_file, 'r') as f:
                self.results = json.load(f)
        else:
            self.results = None
    
    def deduplicate_alerts(self, alerts):
        """
        Remove duplicate player alerts
        
        Returns:
            Dict mapping player name to unique alerts
        """
        deduplicated = {}
        
        for alert_group in alerts:
            player = alert_group['player']
            
            if player not in deduplicated:
                deduplicated[player] = alert_group['alerts']
        
        return deduplicated
    
    def categorize_alerts(self, deduplicated_alerts):
        """
        Categorize alerts by signal type
        
        Returns:
            Dict with 'strong_buy', 'buy', 'sell', 'strong_sell' categories
        """
        categories = {
            'strong_buy': [],      # Multiple Tier 1 BUY signals
            'buy': [],             # Single Tier 1-2 BUY signal
            'strong_sell': [],     # Multiple Tier 1 SELL signals
            'sell': [],            # Single Tier 1-2 SELL signal
            'mixed': []            # Both BUY and SELL signals
        }
        
        for player, alerts in deduplicated_alerts.items():
            tier1_buys = len([a for a in alerts if a['tier'] == 1 and a['signal'] == 'BUY'])
            tier1_sells = len([a for a in alerts if a['tier'] == 1 and a['signal'] == 'SELL'])
            tier2_buys = len([a for a in alerts if a['tier'] == 2 and a['signal'] == 'BUY'])
            tier2_sells = len([a for a in alerts if a['tier'] == 2 and a['signal'] == 'SELL'])
            
            total_buys = tier1_buys + tier2_buys
            total_sells = tier1_sells + tier2_sells
            
            alert_data = {
                'player': player,
                'alerts': alerts,
                'tier1_buys': tier1_buys,
                'tier1_sells': tier1_sells,
                'net_signal': total_buys - total_sells
            }
            
            # Categorize
            if total_buys > 0 and total_sells > 0:
                categories['mixed'].append(alert_data)
            elif tier1_buys >= 2 or (tier1_buys >= 1 and tier2_buys >= 1):
                categories['strong_buy'].append(alert_data)
            elif total_buys > 0:
                categories['buy'].append(alert_data)
            elif tier1_sells >= 2 or (tier1_sells >= 1 and tier2_sells >= 1):
                categories['strong_sell'].append(alert_data)
            elif total_sells > 0:
                categories['sell'].append(alert_data)
        
        return categories
    
    def generate_digest(self):
        """
        Generate formatted alert digest
        
        Returns:
            Formatted string report
        """
        if not self.results or not self.results.get('new_alerts'):
            return "No new alerts to report."
        
        # Deduplicate
        deduplicated = self.deduplicate_alerts(self.results['new_alerts'])
        
        # Categorize
        categories = self.categorize_alerts(deduplicated)
        
        # Build report
        report = []
        report.append("=" * 70)
        report.append(f"REGRESSION ALERT DIGEST - {datetime.now().strftime('%Y-%m-%d')}")
        report.append("=" * 70)
        
        report.append(f"\n📊 Summary:")
        report.append(f"   Total Players with Alerts: {len(deduplicated)}")
        report.append(f"   Strong Buy Signals: {len(categories['strong_buy'])}")
        report.append(f"   Buy Signals: {len(categories['buy'])}")
        report.append(f"   Strong Sell Signals: {len(categories['strong_sell'])}")
        report.append(f"   Sell Signals: {len(categories['sell'])}")
        report.append(f"   Mixed Signals: {len(categories['mixed'])}")
        
        # Strong Buy Candidates
        if categories['strong_buy']:
            report.append("\n\n🟢 STRONG BUY CANDIDATES (Multiple positive signals)")
            report.append("-" * 70)
            
            for item in sorted(categories['strong_buy'], 
                             key=lambda x: x['net_signal'], reverse=True):
                report.append(f"\n📈 {item['player']} (Net: +{item['net_signal']})")
                for alert in item['alerts']:
                    if alert['signal'] == 'BUY':
                        tier_emoji = "🔴" if alert['tier'] == 1 else "🟡"
                        report.append(f"   {tier_emoji} TIER {alert['tier']} {alert['metric']}: {alert['message']}")
        
        # Buy Candidates
        if categories['buy']:
            report.append("\n\n🟢 BUY CANDIDATES")
            report.append("-" * 70)
            
            for item in categories['buy'][:10]:  # Top 10
                report.append(f"\n{item['player']}:")
                for alert in item['alerts']:
                    tier_emoji = "🔴" if alert['tier'] == 1 else "🟡"
                    report.append(f"   {tier_emoji} {alert['metric']}: {alert['message']}")
        
        # Strong Sell Candidates
        if categories['strong_sell']:
            report.append("\n\n🔴 STRONG SELL CANDIDATES (Multiple negative signals)")
            report.append("-" * 70)
            
            for item in sorted(categories['strong_sell'], 
                             key=lambda x: x['net_signal']):
                report.append(f"\n📉 {item['player']} (Net: {item['net_signal']})")
                for alert in item['alerts']:
                    if alert['signal'] == 'SELL':
                        tier_emoji = "🔴" if alert['tier'] == 1 else "🟡"
                        report.append(f"   {tier_emoji} TIER {alert['tier']} {alert['metric']}: {alert['message']}")
        
        # Sell Candidates
        if categories['sell']:
            report.append("\n\n🔴 SELL CANDIDATES")
            report.append("-" * 70)
            
            for item in categories['sell'][:10]:  # Top 10
                report.append(f"\n{item['player']}:")
                for alert in item['alerts']:
                    tier_emoji = "🔴" if alert['tier'] == 1 else "🟡"
                    report.append(f"   {tier_emoji} {alert['metric']}: {alert['message']}")
        
        # Mixed signals
        if categories['mixed']:
            report.append("\n\n⚪ MIXED SIGNALS (Conflicting indicators)")
            report.append("-" * 70)
            
            for item in categories['mixed'][:5]:
                report.append(f"\n{item['player']}:")
                for alert in item['alerts']:
                    tier_emoji = "🔴" if alert['tier'] == 1 else "🟡"
                    signal_emoji = "📈" if alert['signal'] == 'BUY' else "📉"
                    report.append(f"   {tier_emoji} {signal_emoji} {alert['metric']}: {alert['message']}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def save_digest(self, output_file=None):
        """Save digest to file"""
        if not output_file:
            output_file = f"alert_digest_{datetime.now().strftime('%Y%m%d')}.txt"
        
        digest = self.generate_digest()
        
        with open(output_file, 'w') as f:
            f.write(digest)
        
        print(f"📝 Alert digest saved to {output_file}")
        
        return output_file


if __name__ == "__main__":
    # Find most recent daily update file
    update_files = sorted(Path('.').glob('daily_update_*.json'), reverse=True)
    
    if not update_files:
        print("No daily update files found!")
    else:
        latest_file = update_files[0]
        print(f"📊 Processing {latest_file}...\n")
        
        digest = AlertDigest(latest_file)
        report = digest.generate_digest()
        
        print(report)
        
        # Save to file
        digest.save_digest()