#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版收费计算器
集成时间段费率、优惠活动、节假日等复杂计费逻辑
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math
from config import (
    VEHICLE_TYPES, TIME_PERIODS, DISCOUNT_CONFIG, 
    BILLING_CONFIG, get_vehicle_config, get_time_periods, get_discount_config
)

class EnhancedFeeCalculator:
    """增强版收费计算器"""
    
    def __init__(self):
        self.vehicle_configs = VEHICLE_TYPES
        self.time_periods = TIME_PERIODS
        self.discount_configs = DISCOUNT_CONFIG
        self.billing_config = BILLING_CONFIG
    
    def calculate_fee(self, vehicle_type: str, entry_time: datetime, 
                     exit_time: datetime, plate_number: str = None, 
                     user_info: Dict = None) -> Dict:
        """
        计算停车费用
        
        Args:
            vehicle_type: 车辆类型
            entry_time: 入场时间
            exit_time: 离场时间
            plate_number: 车牌号（用于查询用户信息）
            user_info: 用户信息
            
        Returns:
            包含详细计费信息的字典
        """
        if vehicle_type not in self.vehicle_configs:
            raise ValueError(f"未知的车辆类型: {vehicle_type}")
        
        # 基础计费
        base_fee = self._calculate_base_fee(vehicle_type, entry_time, exit_time)
        
        # 时间段费率调整
        time_adjusted_fee = self._apply_time_period_rates(base_fee, entry_time, exit_time)
        
        # 应用优惠
        discount_info = self._apply_discounts(time_adjusted_fee, vehicle_type, user_info, entry_time)
        
        # 计算税费
        tax_amount = self._calculate_tax(discount_info["final_fee"])
        
        # 最终费用
        total_fee = discount_info["final_fee"] + tax_amount
        
        return {
            "vehicle_type": vehicle_type,
            "plate_number": plate_number,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "parking_duration": exit_time - entry_time,
            "base_fee": base_fee,
            "time_adjusted_fee": time_adjusted_fee,
            "discount_info": discount_info,
            "tax_amount": tax_amount,
            "total_fee": total_fee,
            "currency": self.billing_config["currency"],
            "calculation_details": self._get_calculation_details(
                vehicle_type, entry_time, exit_time, base_fee, time_adjusted_fee, discount_info
            )
        }
    
    def _calculate_base_fee(self, vehicle_type: str, entry_time: datetime, exit_time: datetime) -> float:
        """计算基础费用"""
        config = self.vehicle_configs[vehicle_type]
        duration = exit_time - entry_time
        total_hours = duration.total_seconds() / 3600
        
        if vehicle_type == "monthly":
            return self._calculate_monthly_fee(config, duration)
        elif vehicle_type == "prepaid":
            return self._calculate_prepaid_fee(config, total_hours)
        elif vehicle_type == "temporary":
            return self._calculate_temporary_fee(config, total_hours)
        elif vehicle_type == "free":
            return 0.0
        else:
            raise ValueError(f"不支持的车辆类型: {vehicle_type}")
    
    def _calculate_monthly_fee(self, config: Dict, duration: timedelta) -> float:
        """计算月租车费用"""
        days = duration.days
        monthly_fee = config["monthly_fee"]
        
        # 如果超过一个月，超出部分按日费率计算
        if days > config["max_monthly_days"]:
            extra_days = days - config["max_monthly_days"]
            extra_fee = extra_days * config["extra_daily_rate"]
            return monthly_fee + extra_fee
        
        return monthly_fee
    
    def _calculate_prepaid_fee(self, config: Dict, total_hours: float) -> float:
        """计算储值车费用"""
        hourly_fee = total_hours * config["hourly_rate"]
        
        # 计算天数，每天有封顶
        days = math.ceil(total_hours / 24)
        daily_cap_total = days * config["daily_cap"]
        
        return min(hourly_fee, daily_cap_total)
    
    def _calculate_temporary_fee(self, config: Dict, total_hours: float) -> float:
        """计算临停车费用"""
        # 免费停车时间
        if total_hours <= config["free_hours"]:
            return 0.0
        
        # 超出免费时间的部分按小时计费
        billable_hours = total_hours - config["free_hours"]
        hourly_fee = billable_hours * config["hourly_rate"]
        
        # 计算天数，每天有封顶
        days = math.ceil(total_hours / 24)
        daily_cap_total = days * config["daily_cap"]
        
        return min(hourly_fee, daily_cap_total)
    
    def _apply_time_period_rates(self, base_fee: float, entry_time: datetime, exit_time: datetime) -> float:
        """应用时间段费率"""
        if base_fee == 0:
            return 0.0
        
        # 计算每个时间段的费用
        total_adjusted_fee = 0.0
        current_time = entry_time
        
        while current_time < exit_time:
            # 找到当前时间所属的时间段
            period_rate = self._get_period_rate(current_time)
            
            # 计算到下一个小时或结束时间的时长
            next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            end_time = min(next_hour, exit_time)
            
            # 计算这个时间段的费用比例
            duration_hours = (end_time - current_time).total_seconds() / 3600
            period_fee = (base_fee / 24) * duration_hours * period_rate
            
            total_adjusted_fee += period_fee
            current_time = end_time
        
        return total_adjusted_fee
    
    def _get_period_rate(self, time: datetime) -> float:
        """获取指定时间的费率倍数"""
        hour = time.hour
        is_weekend = time.weekday() >= 5  # 周六、周日
        
        # 检查是否在特殊时间段内
        for period_name, period_config in self.time_periods.items():
            start_hour = int(period_config["start"].split(":")[0])
            end_hour = int(period_config["end"].split(":")[0])
            
            if start_hour <= end_hour:  # 同一天内
                if start_hour <= hour < end_hour:
                    return period_config["rate_multiplier"]
            else:  # 跨天（如夜间22:00-06:00）
                if hour >= start_hour or hour < end_hour:
                    return period_config["rate_multiplier"]
        
        # 默认费率
        return 1.0
    
    def _apply_discounts(self, fee: float, vehicle_type: str, user_info: Dict, entry_time: datetime) -> Dict:
        """应用优惠折扣"""
        original_fee = fee
        applied_discounts = []
        final_fee = fee
        
        # 新用户折扣
        if user_info and self._is_new_user(user_info):
            new_user_config = self.discount_configs["new_user_discount"]
            if fee >= new_user_config["min_amount"]:
                discount_amount = fee * (1 - new_user_config["rate"])
                final_fee -= discount_amount
                applied_discounts.append({
                    "type": "new_user",
                    "description": "新用户优惠",
                    "rate": new_user_config["rate"],
                    "amount": discount_amount
                })
        
        # 节假日折扣
        if self._is_holiday(entry_time):
            holiday_config = self.discount_configs["holiday_discount"]
            discount_amount = final_fee * (1 - holiday_config["rate"])
            final_fee -= discount_amount
            applied_discounts.append({
                "type": "holiday",
                "description": "节假日优惠",
                "rate": holiday_config["rate"],
                "amount": discount_amount
            })
        
        # 忠诚度折扣
        if user_info and vehicle_type == "monthly":
            loyalty_discount = self._get_loyalty_discount(user_info)
            if loyalty_discount > 0:
                discount_amount = final_fee * (1 - loyalty_discount)
                final_fee -= discount_amount
                applied_discounts.append({
                    "type": "loyalty",
                    "description": "忠诚度优惠",
                    "rate": loyalty_discount,
                    "amount": discount_amount
                })
        
        # 月租车基础折扣
        if vehicle_type == "monthly":
            monthly_config = self.vehicle_configs["monthly"]
            discount_amount = final_fee * (1 - monthly_config["discount_rate"])
            final_fee -= discount_amount
            applied_discounts.append({
                "type": "monthly",
                "description": "月租优惠",
                "rate": monthly_config["discount_rate"],
                "amount": discount_amount
            })
        
        return {
            "original_fee": original_fee,
            "applied_discounts": applied_discounts,
            "total_discount": original_fee - final_fee,
            "final_fee": final_fee
        }
    
    def _is_new_user(self, user_info: Dict) -> bool:
        """判断是否为新用户"""
        if not user_info or "registration_date" not in user_info:
            return False
        
        try:
            reg_date = datetime.fromisoformat(user_info["registration_date"])
            days_since_reg = (datetime.now() - reg_date).days
            return days_since_reg <= self.discount_configs["new_user_discount"]["valid_days"]
        except:
            return False
    
    def _is_holiday(self, time: datetime) -> bool:
        """判断是否为节假日"""
        holiday_dates = self.discount_configs["holiday_discount"]["valid_dates"]
        current_date = time.strftime("%m-%d")
        return current_date in holiday_dates
    
    def _get_loyalty_discount(self, user_info: Dict) -> float:
        """获取忠诚度折扣"""
        if not user_info or "contract_start_date" not in user_info:
            return 0.0
        
        try:
            contract_start = datetime.fromisoformat(user_info["contract_start_date"])
            months_since_start = (datetime.now() - contract_start).days / 30
            
            loyalty_tiers = self.discount_configs["loyalty_discount"]["tiers"]
            for tier in sorted(loyalty_tiers, key=lambda x: x["months"], reverse=True):
                if months_since_start >= tier["months"]:
                    return tier["discount"]
        except:
            pass
        
        return 0.0
    
    def _calculate_tax(self, fee: float) -> float:
        """计算税费"""
        return fee * self.billing_config["tax_rate"]
    
    def _get_calculation_details(self, vehicle_type: str, entry_time: datetime, 
                                exit_time: datetime, base_fee: float, 
                                time_adjusted_fee: float, discount_info: Dict) -> Dict:
        """获取计费详情"""
        return {
            "vehicle_type_config": self.vehicle_configs[vehicle_type],
            "time_periods_applied": self._get_applied_time_periods(entry_time, exit_time),
            "discount_breakdown": discount_info["applied_discounts"],
            "fee_breakdown": {
                "base_fee": base_fee,
                "time_adjustment": time_adjusted_fee - base_fee,
                "discounts": discount_info["total_discount"],
                "final_fee_before_tax": discount_info["final_fee"]
            }
        }
    
    def _get_applied_time_periods(self, entry_time: datetime, exit_time: datetime) -> List[Dict]:
        """获取应用的时间段信息"""
        periods = []
        current_time = entry_time
        
        while current_time < exit_time:
            period_rate = self._get_period_rate(current_time)
            period_name = self._get_period_name(current_time)
            
            next_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            end_time = min(next_hour, exit_time)
            
            duration_hours = (end_time - current_time).total_seconds() / 3600
            
            periods.append({
                "period": period_name,
                "start_time": current_time,
                "end_time": end_time,
                "duration_hours": duration_hours,
                "rate_multiplier": period_rate
            })
            
            current_time = end_time
        
        return periods
    
    def _get_period_name(self, time: datetime) -> str:
        """获取时间段名称"""
        hour = time.hour
        
        for period_name, period_config in self.time_periods.items():
            start_hour = int(period_config["start"].split(":")[0])
            end_hour = int(period_config["end"].split(":")[0])
            
            if start_hour <= end_hour:  # 同一天内
                if start_hour <= hour < end_hour:
                    return period_config["description"]
            else:  # 跨天
                if hour >= start_hour or hour < end_hour:
                    return period_config["description"]
        
        return "标准时段"

def demo_enhanced_calculator():
    """演示增强版收费计算器"""
    print("=== 增强版收费计算器演示 ===\n")
    
    calculator = EnhancedFeeCalculator()
    
    # 测试用例1：月租车
    print("测试用例1：月租车")
    entry_time = datetime(2024, 1, 15, 8, 0, 0)  # 早高峰
    exit_time = datetime(2024, 1, 15, 18, 0, 0)  # 晚高峰
    user_info = {
        "registration_date": "2024-01-01T00:00:00",
        "contract_start_date": "2024-01-01T00:00:00"
    }
    
    result = calculator.calculate_fee("monthly", entry_time, exit_time, "京A12345", user_info)
    print(f"入场时间: {entry_time}")
    print(f"离场时间: {exit_time}")
    print(f"停车时长: {result['parking_duration']}")
    print(f"基础费用: ¥{result['base_fee']:.2f}")
    print(f"时段调整后: ¥{result['time_adjusted_fee']:.2f}")
    print(f"优惠后费用: ¥{result['discount_info']['final_fee']:.2f}")
    print(f"税费: ¥{result['tax_amount']:.2f}")
    print(f"最终费用: ¥{result['total_fee']:.2f}")
    
    # 显示优惠详情
    print("\n优惠详情:")
    for discount in result['discount_info']['applied_discounts']:
        print(f"  {discount['description']}: {discount['rate']:.1%} 优惠，节省 ¥{discount['amount']:.2f}")
    
    # 显示时间段详情
    print("\n时间段详情:")
    for period in result['calculation_details']['time_periods_applied']:
        print(f"  {period['period']}: {period['start_time'].strftime('%H:%M')}-{period['end_time'].strftime('%H:%M')}, "
              f"时长 {period['duration_hours']:.1f}小时, 费率倍数 {period['rate_multiplier']}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例2：临停车
    print("测试用例2：临停车")
    entry_time = datetime(2024, 1, 15, 22, 0, 0)  # 夜间
    exit_time = datetime(2024, 1, 16, 6, 0, 0)    # 夜间
    
    result = calculator.calculate_fee("temporary", entry_time, exit_time, "京B67890")
    print(f"入场时间: {entry_time}")
    print(f"离场时间: {exit_time}")
    print(f"停车时长: {result['parking_duration']}")
    print(f"基础费用: ¥{result['base_fee']:.2f}")
    print(f"时段调整后: ¥{result['time_adjusted_fee']:.2f}")
    print(f"最终费用: ¥{result['total_fee']:.2f}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例3：储值车
    print("测试用例3：储值车")
    entry_time = datetime(2024, 1, 15, 10, 0, 0)  # 平峰时段
    exit_time = datetime(2024, 1, 15, 16, 0, 0)   # 平峰时段
    
    result = calculator.calculate_fee("prepaid", entry_time, exit_time, "京C11111")
    print(f"入场时间: {entry_time}")
    print(f"离场时间: {exit_time}")
    print(f"停车时长: {result['parking_duration']}")
    print(f"基础费用: ¥{result['base_fee']:.2f}")
    print(f"时段调整后: ¥{result['time_adjusted_fee']:.2f}")
    print(f"最终费用: ¥{result['total_fee']:.2f}")

if __name__ == "__main__":
    demo_enhanced_calculator()