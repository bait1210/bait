#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停车场管理系统测试文件
测试各项功能和边界条件
"""

import unittest
from datetime import datetime, timedelta
from parking_system import (
    ParkingSystem, ParkingLot, Vehicle, VehicleType,
    MonthlyVehicleFeeCalculator, PrepaidVehicleFeeCalculator,
    TemporaryVehicleFeeCalculator, FreeVehicleFeeCalculator
)
from enhanced_fee_calculator import EnhancedFeeCalculator
from config import VEHICLE_TYPES, validate_config

class TestParkingSystem(unittest.TestCase):
    """停车场管理系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.system = ParkingSystem()
        self.system.create_parking_lot("测试停车场", 10)
        self.parking_lot = self.system.parking_lots["测试停车场"]
        
        # 注册测试车辆
        self.system.register_vehicle("测试月租车", VehicleType.MONTHLY)
        self.system.register_vehicle("测试储值车", VehicleType.PREPAID)
        self.system.register_vehicle("测试临停车", VehicleType.TEMPORARY)
        self.system.register_vehicle("测试免费车", VehicleType.FREE)
    
    def test_vehicle_registration(self):
        """测试车辆注册功能"""
        # 测试正常注册
        result = self.system.register_vehicle("新车辆", VehicleType.MONTHLY)
        self.assertTrue(result)
        
        # 测试重复注册
        result = self.system.register_vehicle("新车辆", VehicleType.MONTHLY)
        self.assertFalse(result)
        
        # 测试获取注册信息
        info = self.system.get_vehicle_registry_info("测试月租车")
        self.assertIsNotNone(info)
        self.assertEqual(info["vehicle_type"], VehicleType.MONTHLY)
    
    def test_parking_lot_creation(self):
        """测试停车场创建功能"""
        # 测试正常创建
        result = self.system.create_parking_lot("新停车场", 50)
        self.assertTrue(result)
        
        # 测试重复创建
        result = self.system.create_parking_lot("新停车场", 50)
        self.assertFalse(result)
        
        # 测试获取停车场
        self.assertIn("新停车场", self.system.parking_lots)
    
    def test_vehicle_entry_exit(self):
        """测试车辆进出功能"""
        # 测试车辆入场
        result = self.parking_lot.enter_parking("测试月租车", VehicleType.MONTHLY)
        self.assertTrue(result)
        self.assertEqual(self.parking_lot.occupied_spaces, 1)
        
        # 测试重复入场
        result = self.parking_lot.enter_parking("测试月租车", VehicleType.MONTHLY)
        self.assertFalse(result)
        
        # 测试车辆离场
        fee = self.parking_lot.exit_parking("测试月租车")
        self.assertIsNotNone(fee)
        self.assertEqual(self.parking_lot.occupied_spaces, 0)
        
        # 测试离场不存在的车辆
        fee = self.parking_lot.exit_parking("不存在的车辆")
        self.assertIsNone(fee)
    
    def test_parking_lot_capacity(self):
        """测试停车场容量限制"""
        # 填满停车场
        for i in range(10):
            plate_number = f"车辆{i}"
            self.system.register_vehicle(plate_number, VehicleType.TEMPORARY)
            result = self.parking_lot.enter_parking(plate_number, VehicleType.TEMPORARY)
            self.assertTrue(result)
        
        # 测试超出容量
        self.system.register_vehicle("超出车辆", VehicleType.TEMPORARY)
        result = self.parking_lot.enter_parking("超出车辆", VehicleType.TEMPORARY)
        self.assertFalse(result)
    
    def test_parking_status(self):
        """测试停车场状态查询"""
        # 入场一辆车
        self.parking_lot.enter_parking("测试月租车", VehicleType.MONTHLY)
        
        # 获取状态
        status = self.parking_lot.get_parking_status()
        self.assertEqual(status["name"], "测试停车场")
        self.assertEqual(status["total_spaces"], 10)
        self.assertEqual(status["occupied_spaces"], 1)
        self.assertEqual(status["available_spaces"], 9)
        self.assertEqual(status["occupancy_rate"], 10.0)
    
    def test_statistics(self):
        """测试统计功能"""
        # 入场不同类型的车辆
        self.parking_lot.enter_parking("测试月租车", VehicleType.MONTHLY)
        self.parking_lot.enter_parking("测试储值车", VehicleType.PREPAID)
        
        # 离场并产生费用
        self.parking_lot.exit_parking("测试月租车")
        self.parking_lot.exit_parking("测试储值车")
        
        # 检查统计
        stats = self.parking_lot.get_statistics()
        self.assertGreater(stats[VehicleType.MONTHLY]["revenue"], 0)
        self.assertGreater(stats[VehicleType.PREPAID]["revenue"], 0)
    
    def test_system_summary(self):
        """测试系统总览"""
        summary = self.system.get_system_summary()
        self.assertEqual(summary["total_parking_lots"], 2)  # 测试停车场 + 新停车场
        self.assertEqual(summary["registered_vehicles"], 4)  # 4辆测试车辆

class TestFeeCalculators(unittest.TestCase):
    """收费计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.entry_time = datetime(2024, 1, 15, 10, 0, 0)
        self.exit_time = datetime(2024, 1, 15, 12, 0, 0)  # 2小时
        
        self.monthly_calc = MonthlyVehicleFeeCalculator()
        self.prepaid_calc = PrepaidVehicleFeeCalculator()
        self.temporary_calc = TemporaryVehicleFeeCalculator()
        self.free_calc = FreeVehicleFeeCalculator()
    
    def test_monthly_calculator(self):
        """测试月租车收费计算器"""
        vehicle = Vehicle("测试车辆", VehicleType.MONTHLY, self.entry_time)
        vehicle.exit_parking(self.exit_time)
        
        fee = self.monthly_calc.calculate_fee(vehicle)
        self.assertEqual(fee, 300.0)  # 月租费用
        
        # 测试超出月租时间
        long_exit_time = self.entry_time + timedelta(days=35)
        vehicle.exit_time = long_exit_time
        vehicle.parking_duration = long_exit_time - self.entry_time
        
        fee = self.monthly_calc.calculate_fee(vehicle)
        expected_fee = 300.0 + (5 * 20.0)  # 月租 + 5天额外费用
        self.assertEqual(fee, expected_fee)
    
    def test_prepaid_calculator(self):
        """测试储值车收费计算器"""
        vehicle = Vehicle("测试车辆", VehicleType.PREPAID, self.entry_time)
        vehicle.exit_parking(self.exit_time)
        
        fee = self.prepaid_calc.calculate_fee(vehicle)
        expected_fee = 2 * 5.0  # 2小时 * ¥5/小时
        self.assertEqual(fee, expected_fee)
        
        # 测试日封顶
        long_exit_time = self.entry_time + timedelta(hours=15)  # 15小时
        vehicle.exit_time = long_exit_time
        vehicle.parking_duration = long_exit_time - self.entry_time
        
        fee = self.prepaid_calc.calculate_fee(vehicle)
        hourly_fee = 15 * 5.0  # 15小时 * ¥5/小时
        daily_cap = 50.0  # 日封顶
        expected_fee = min(hourly_fee, daily_cap)
        self.assertEqual(fee, expected_fee)
    
    def test_temporary_calculator(self):
        """测试临停车收费计算器"""
        vehicle = Vehicle("测试车辆", VehicleType.TEMPORARY, self.entry_time)
        vehicle.exit_parking(self.exit_time)
        
        fee = self.temporary_calc.calculate_fee(vehicle)
        # 首小时免费，第二小时收费
        expected_fee = 1 * 8.0  # 1小时 * ¥8/小时
        self.assertEqual(fee, expected_fee)
        
        # 测试短时间停车（免费）
        short_exit_time = self.entry_time + timedelta(minutes=30)
        vehicle.exit_time = short_exit_time
        vehicle.parking_duration = short_exit_time - self.entry_time
        
        fee = self.temporary_calc.calculate_fee(vehicle)
        self.assertEqual(fee, 0.0)  # 30分钟免费
    
    def test_free_calculator(self):
        """测试免费车收费计算器"""
        vehicle = Vehicle("测试车辆", VehicleType.FREE, self.entry_time)
        vehicle.exit_parking(self.exit_time)
        
        fee = self.free_calc.calculate_fee(vehicle)
        self.assertEqual(fee, 0.0)

class TestEnhancedFeeCalculator(unittest.TestCase):
    """增强版收费计算器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calculator = EnhancedFeeCalculator()
        self.entry_time = datetime(2024, 1, 15, 8, 0, 0)  # 早高峰
        self.exit_time = datetime(2024, 1, 15, 18, 0, 0)  # 晚高峰
        self.user_info = {
            "registration_date": "2024-01-01T00:00:00",
            "contract_start_date": "2024-01-01T00:00:00"
        }
    
    def test_monthly_vehicle_with_discounts(self):
        """测试月租车优惠计算"""
        result = self.calculator.calculate_fee(
            "monthly", self.entry_time, self.exit_time, 
            "测试车辆", self.user_info
        )
        
        self.assertIn("vehicle_type", result)
        self.assertIn("total_fee", result)
        self.assertIn("discount_info", result)
        self.assertIn("calculation_details", result)
        
        # 检查优惠信息
        discounts = result["discount_info"]["applied_discounts"]
        self.assertGreater(len(discounts), 0)
        
        # 检查时间段信息
        time_periods = result["calculation_details"]["time_periods_applied"]
        self.assertGreater(len(time_periods), 0)
    
    def test_time_period_rates(self):
        """测试时间段费率"""
        # 测试夜间费率
        night_entry = datetime(2024, 1, 15, 22, 0, 0)
        night_exit = datetime(2024, 1, 16, 6, 0, 0)
        
        result = self.calculator.calculate_fee("temporary", night_entry, night_exit)
        
        # 夜间应该有费率调整
        time_periods = result["calculation_details"]["time_periods_applied"]
        night_periods = [p for p in time_periods if "夜间" in p["period"]]
        self.assertGreater(len(night_periods), 0)
    
    def test_holiday_discount(self):
        """测试节假日优惠"""
        # 测试元旦
        holiday_entry = datetime(2024, 1, 1, 10, 0, 0)
        holiday_exit = datetime(2024, 1, 1, 12, 0, 0)
        
        result = self.calculator.calculate_fee("temporary", holiday_entry, holiday_exit)
        
        # 检查是否有节假日优惠
        discounts = result["discount_info"]["applied_discounts"]
        holiday_discounts = [d for d in discounts if d["type"] == "holiday"]
        self.assertGreater(len(holiday_discounts), 0)

class TestConfiguration(unittest.TestCase):
    """配置测试类"""
    
    def test_config_validation(self):
        """测试配置验证"""
        result = validate_config()
        self.assertTrue(result)
    
    def test_vehicle_type_configs(self):
        """测试车辆类型配置"""
        # 检查月租车配置
        monthly_config = VEHICLE_TYPES["monthly"]
        self.assertIn("monthly_fee", monthly_config)
        self.assertIn("extra_daily_rate", monthly_config)
        self.assertIn("discount_rate", monthly_config)
        
        # 检查储值车配置
        prepaid_config = VEHICLE_TYPES["prepaid"]
        self.assertIn("hourly_rate", prepaid_config)
        self.assertIn("daily_cap", prepaid_config)
        
        # 检查临停车配置
        temporary_config = VEHICLE_TYPES["temporary"]
        self.assertIn("hourly_rate", temporary_config)
        self.assertIn("daily_cap", temporary_config)
        self.assertIn("free_hours", temporary_config)
        
        # 检查免费车配置
        free_config = VEHICLE_TYPES["free"]
        self.assertIn("fee", free_config)
        self.assertIn("max_duration", free_config)

def run_performance_test():
    """性能测试"""
    print("=== 性能测试 ===")
    
    system = ParkingSystem()
    system.create_parking_lot("性能测试停车场", 1000)
    
    # 批量注册车辆
    start_time = datetime.now()
    for i in range(1000):
        plate_number = f"性能测试车辆{i:04d}"
        system.register_vehicle(plate_number, VehicleType.TEMPORARY)
    
    registration_time = (datetime.now() - start_time).total_seconds()
    print(f"注册1000辆车耗时: {registration_time:.3f}秒")
    
    # 批量入场
    parking_lot = system.parking_lots["性能测试停车场"]
    start_time = datetime.now()
    for i in range(1000):
        plate_number = f"性能测试车辆{i:04d}"
        parking_lot.enter_parking(plate_number, VehicleType.TEMPORARY)
    
    entry_time = (datetime.now() - start_time).total_seconds()
    print(f"1000辆车入场耗时: {entry_time:.3f}秒")
    
    # 批量离场
    start_time = datetime.now()
    total_fee = 0
    for i in range(1000):
        plate_number = f"性能测试车辆{i:04d}"
        fee = parking_lot.exit_parking(plate_number)
        if fee:
            total_fee += fee
    
    exit_time = (datetime.now() - start_time).total_seconds()
    print(f"1000辆车离场耗时: {exit_time:.3f}秒")
    print(f"总收入: ¥{total_fee:.2f}")
    
    # 系统总览
    summary = system.get_system_summary()
    print(f"系统总览: {summary}")

if __name__ == "__main__":
    # 运行单元测试
    print("=== 运行单元测试 ===")
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "="*50 + "\n")
    
    # 运行性能测试
    run_performance_test()