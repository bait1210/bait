#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停车场管理系统配置文件
定义各种车辆类型的收费规则和参数
"""

# 车辆类型配置
VEHICLE_TYPES = {
    "monthly": {
        "name": "月租车",
        "description": "按月包月收费，适合长期停车用户",
        "monthly_fee": 300.0,  # 月租费用
        "extra_daily_rate": 20.0,  # 超出月租后的日费率
        "max_monthly_days": 30,  # 月租包含的最大天数
        "discount_rate": 0.8,  # 月租折扣率
        "min_contract_months": 1,  # 最少签约月数
    },
    
    "prepaid": {
        "name": "储值车",
        "description": "预付费模式，按小时计费，有日封顶",
        "hourly_rate": 5.0,  # 小时费率
        "daily_cap": 50.0,  # 日封顶金额
        "min_balance": 10.0,  # 最低余额警告
        "bonus_rate": 0.05,  # 充值赠送比例
        "bonus_threshold": 100.0,  # 充值赠送门槛
    },
    
    "temporary": {
        "name": "临停车",
        "description": "临时停车，按小时计费，有日封顶",
        "hourly_rate": 8.0,  # 小时费率
        "daily_cap": 80.0,  # 日封顶金额
        "free_hours": 1,  # 免费停车小时数
        "night_rate": 0.5,  # 夜间费率折扣（22:00-06:00）
        "weekend_rate": 1.2,  # 周末费率上浮
    },
    
    "free": {
        "name": "免费车",
        "description": "特殊车辆，不收费",
        "fee": 0.0,  # 固定费用
        "max_duration": 24,  # 最大停车时长（小时）
        "requires_approval": True,  # 是否需要审批
        "approval_level": "manager",  # 审批级别
    }
}

# 停车场配置
PARKING_LOT_CONFIG = {
    "default_capacity": 100,  # 默认停车场容量
    "max_capacity": 1000,  # 最大停车场容量
    "reserved_spaces": 0.1,  # 预留车位比例
    "overflow_allowed": True,  # 是否允许超载
    "max_overflow": 0.2,  # 最大超载比例
}

# 计费规则配置
BILLING_CONFIG = {
    "currency": "CNY",  # 货币单位
    "decimal_places": 2,  # 小数位数
    "rounding_method": "round",  # 舍入方法：round, ceil, floor
    "tax_rate": 0.06,  # 税率
    "late_fee_rate": 0.05,  # 滞纳金费率（每日）
    "max_late_fee": 0.5,  # 最大滞纳金比例
}

# 时间段配置
TIME_PERIODS = {
    "peak_hours": {
        "start": "07:00",
        "end": "09:00",
        "rate_multiplier": 1.5,  # 高峰时段费率倍数
        "description": "早高峰"
    },
    "off_peak_hours": {
        "start": "10:00",
        "end": "16:00",
        "rate_multiplier": 0.8,  # 平峰时段费率倍数
        "description": "平峰时段"
    },
    "evening_peak": {
        "start": "17:00",
        "end": "19:00",
        "rate_multiplier": 1.3,  # 晚高峰费率倍数
        "description": "晚高峰"
    },
    "night_hours": {
        "start": "22:00",
        "end": "06:00",
        "rate_multiplier": 0.5,  # 夜间费率倍数
        "description": "夜间时段"
    }
}

# 优惠活动配置
DISCOUNT_CONFIG = {
    "new_user_discount": {
        "rate": 0.9,  # 新用户折扣
        "valid_days": 30,  # 有效期（天）
        "min_amount": 50.0,  # 最低消费金额
    },
    "holiday_discount": {
        "rate": 0.8,  # 节假日折扣
        "valid_dates": [
            "01-01",  # 元旦
            "05-01",  # 劳动节
            "10-01",  # 国庆节
        ],
        "description": "节假日优惠"
    },
    "loyalty_discount": {
        "tiers": [
            {"months": 3, "discount": 0.95},   # 3个月以上95折
            {"months": 6, "discount": 0.90},   # 6个月以上9折
            {"months": 12, "discount": 0.85},  # 12个月以上85折
        ],
        "description": "忠诚度折扣"
    }
}

# 系统配置
SYSTEM_CONFIG = {
    "max_vehicles_per_user": 5,  # 每个用户最多车辆数
    "session_timeout": 3600,  # 会话超时时间（秒）
    "max_login_attempts": 5,  # 最大登录尝试次数
    "password_min_length": 8,  # 密码最小长度
    "auto_logout": True,  # 是否自动登出
}

# 通知配置
NOTIFICATION_CONFIG = {
    "sms_enabled": True,  # 短信通知
    "email_enabled": True,  # 邮件通知
    "push_notification": True,  # 推送通知
    "low_balance_threshold": 20.0,  # 低余额提醒阈值
    "expiry_reminder_days": 7,  # 到期提醒天数
}

# 报表配置
REPORT_CONFIG = {
    "daily_report": True,  # 日报
    "weekly_report": True,  # 周报
    "monthly_report": True,  # 月报
    "yearly_report": True,  # 年报
    "auto_generate": True,  # 自动生成
    "retention_days": 365,  # 保留天数
}

def get_vehicle_config(vehicle_type: str) -> dict:
    """获取指定车辆类型的配置"""
    return VEHICLE_TYPES.get(vehicle_type, {})

def get_billing_config() -> dict:
    """获取计费配置"""
    return BILLING_CONFIG

def get_time_periods() -> dict:
    """获取时间段配置"""
    return TIME_PERIODS

def get_discount_config() -> dict:
    """获取优惠配置"""
    return DISCOUNT_CONFIG

def validate_config() -> bool:
    """验证配置的有效性"""
    try:
        # 验证车辆类型配置
        for vehicle_type, config in VEHICLE_TYPES.items():
            if vehicle_type == "monthly":
                assert config["monthly_fee"] > 0
                assert config["extra_daily_rate"] > 0
            elif vehicle_type == "prepaid":
                assert config["hourly_rate"] > 0
                assert config["daily_cap"] > 0
            elif vehicle_type == "temporary":
                assert config["hourly_rate"] > 0
                assert config["daily_cap"] > 0
        
        # 验证计费配置
        assert BILLING_CONFIG["tax_rate"] >= 0
        assert BILLING_CONFIG["late_fee_rate"] >= 0
        
        # 验证时间段配置
        for period, config in TIME_PERIODS.items():
            assert 0 < config["rate_multiplier"] <= 3  # 费率倍数合理范围
        
        return True
        
    except AssertionError:
        return False
    except Exception:
        return False

if __name__ == "__main__":
    # 测试配置
    print("=== 停车场管理系统配置测试 ===")
    
    if validate_config():
        print("✓ 配置验证通过")
        
        # 显示车辆类型配置
        print("\n车辆类型配置:")
        for vehicle_type, config in VEHICLE_TYPES.items():
            print(f"  {config['name']}: {config['description']}")
            
        # 显示计费配置
        print(f"\n计费配置:")
        print(f"  货币单位: {BILLING_CONFIG['currency']}")
        print(f"  税率: {BILLING_CONFIG['tax_rate']:.1%}")
        
        # 显示时间段配置
        print(f"\n时间段配置:")
        for period, config in TIME_PERIODS.items():
            print(f"  {config['description']}: {config['start']}-{config['end']}, 费率倍数: {config['rate_multiplier']}")
            
    else:
        print("✗ 配置验证失败")