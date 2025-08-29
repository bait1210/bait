#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停车场管理系统
支持月租车、储值车、临停车、免费车四种车辆类型
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VehicleType:
    """车辆类型枚举"""
    MONTHLY = "monthly"      # 月租车
    PREPAID = "prepaid"      # 储值车
    TEMPORARY = "temporary"  # 临停车
    FREE = "free"            # 免费车

class Vehicle:
    """车辆基类"""
    def __init__(self, plate_number: str, vehicle_type: str, entry_time: datetime = None):
        self.plate_number = plate_number
        self.vehicle_type = vehicle_type
        self.entry_time = entry_time or datetime.now()
        self.exit_time = None
        self.parking_duration = None
        self.fee = 0.0
        
    def exit_parking(self, exit_time: datetime = None):
        """车辆离场"""
        self.exit_time = exit_time or datetime.now()
        self.parking_duration = self.exit_time - self.entry_time
        
    def __str__(self):
        return f"车牌号: {self.plate_number}, 类型: {self.vehicle_type}, 入场时间: {self.entry_time}"

class FeeCalculator(ABC):
    """收费计算器抽象基类"""
    
    @abstractmethod
    def calculate_fee(self, vehicle: Vehicle) -> float:
        """计算停车费用"""
        pass

class MonthlyVehicleFeeCalculator(FeeCalculator):
    """月租车收费计算器"""
    
    def __init__(self, monthly_fee: float = 300.0):
        self.monthly_fee = monthly_fee
    
    def calculate_fee(self, vehicle: Vehicle) -> float:
        """月租车按包月收费，超出部分按临停车计费"""
        if not vehicle.parking_duration:
            return 0.0
            
        # 月租车基础费用
        base_fee = self.monthly_fee
        
        # 如果超过一个月，超出部分按临停车计费
        days_parked = vehicle.parking_duration.days
        if days_parked > 30:
            extra_days = days_parked - 30
            # 超出部分按每天20元计算
            extra_fee = extra_days * 20.0
            base_fee += extra_fee
            
        return base_fee

class PrepaidVehicleFeeCalculator(FeeCalculator):
    """储值车收费计算器"""
    
    def __init__(self, hourly_rate: float = 5.0, daily_cap: float = 50.0):
        self.hourly_rate = hourly_rate
        self.daily_cap = daily_cap
    
    def calculate_fee(self, vehicle: Vehicle) -> float:
        """储值车按小时计费，有日封顶"""
        if not vehicle.parking_duration:
            return 0.0
            
        total_hours = vehicle.parking_duration.total_seconds() / 3600
        
        # 按小时计费
        hourly_fee = total_hours * self.hourly_rate
        
        # 计算天数，每天有封顶
        days = int(total_hours / 24) + (1 if total_hours % 24 > 0 else 0)
        daily_cap_total = days * self.daily_cap
        
        # 取较小值
        return min(hourly_fee, daily_cap_total)

class TemporaryVehicleFeeCalculator(FeeCalculator):
    """临停车收费计算器"""
    
    def __init__(self, hourly_rate: float = 8.0, daily_cap: float = 80.0):
        self.hourly_rate = hourly_rate
        self.daily_cap = daily_cap
    
    def calculate_fee(self, vehicle: Vehicle) -> float:
        """临停车按小时计费，有日封顶"""
        if not vehicle.parking_duration:
            return 0.0
            
        total_hours = vehicle.parking_duration.total_seconds() / 3600
        
        # 按小时计费
        hourly_fee = total_hours * self.hourly_rate
        
        # 计算天数，每天有封顶
        days = int(total_hours / 24) + (1 if total_hours % 24 > 0 else 0)
        daily_cap_total = days * self.daily_cap
        
        # 取较小值
        return min(hourly_fee, daily_cap_total)

class FreeVehicleFeeCalculator(FeeCalculator):
    """免费车收费计算器"""
    
    def calculate_fee(self, vehicle: Vehicle) -> float:
        """免费车不收费"""
        return 0.0

class ParkingLot:
    """停车场类"""
    
    def __init__(self, name: str, total_spaces: int):
        self.name = name
        self.total_spaces = total_spaces
        self.occupied_spaces = 0
        self.vehicles: Dict[str, Vehicle] = {}
        
        # 初始化收费计算器
        self.fee_calculators = {
            VehicleType.MONTHLY: MonthlyVehicleFeeCalculator(),
            VehicleType.PREPAID: PrepaidVehicleFeeCalculator(),
            VehicleType.TEMPORARY: TemporaryVehicleFeeCalculator(),
            VehicleType.FREE: FreeVehicleFeeCalculator()
        }
        
        # 统计信息
        self.stats = {
            VehicleType.MONTHLY: {"count": 0, "revenue": 0.0},
            VehicleType.PREPAID: {"count": 0, "revenue": 0.0},
            VehicleType.TEMPORARY: {"count": 0, "revenue": 0.0},
            VehicleType.FREE: {"count": 0, "revenue": 0.0}
        }
    
    def enter_parking(self, plate_number: str, vehicle_type: str) -> bool:
        """车辆入场"""
        if self.occupied_spaces >= self.total_spaces:
            logger.warning(f"停车场已满，无法容纳车牌号 {plate_number}")
            return False
            
        if plate_number in self.vehicles:
            logger.warning(f"车牌号 {plate_number} 已在停车场内")
            return False
            
        vehicle = Vehicle(plate_number, vehicle_type)
        self.vehicles[plate_number] = vehicle
        self.occupied_spaces += 1
        self.stats[vehicle_type]["count"] += 1
        
        logger.info(f"车辆入场: {vehicle}")
        return True
    
    def exit_parking(self, plate_number: str) -> Optional[float]:
        """车辆离场并计算费用"""
        if plate_number not in self.vehicles:
            logger.warning(f"车牌号 {plate_number} 不在停车场内")
            return None
            
        vehicle = self.vehicles[plate_number]
        vehicle.exit_parking()
        
        # 计算费用
        calculator = self.fee_calculators.get(vehicle.vehicle_type)
        if calculator:
            fee = calculator.calculate_fee(vehicle)
            vehicle.fee = fee
            self.stats[vehicle.vehicle_type]["revenue"] += fee
            
            logger.info(f"车辆离场: {vehicle}, 费用: ¥{fee:.2f}")
            
            # 移除车辆
            del self.vehicles[plate_number]
            self.occupied_spaces -= 1
            
            return fee
        else:
            logger.error(f"未知的车辆类型: {vehicle.vehicle_type}")
            return None
    
    def get_vehicle_info(self, plate_number: str) -> Optional[Vehicle]:
        """获取车辆信息"""
        return self.vehicles.get(plate_number)
    
    def get_parking_status(self) -> Dict:
        """获取停车场状态"""
        return {
            "name": self.name,
            "total_spaces": self.total_spaces,
            "occupied_spaces": self.occupied_spaces,
            "available_spaces": self.total_spaces - self.occupied_spaces,
            "occupancy_rate": (self.occupied_spaces / self.total_spaces) * 100 if self.total_spaces > 0 else 0
        }
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def get_total_revenue(self) -> float:
        """获取总收入"""
        return sum(stats["revenue"] for stats in self.stats.values())

class ParkingSystem:
    """停车场管理系统主类"""
    
    def __init__(self):
        self.parking_lots: Dict[str, ParkingLot] = {}
        self.vehicle_registry: Dict[str, Dict] = {}  # 车辆注册信息
        
    def create_parking_lot(self, name: str, total_spaces: int) -> bool:
        """创建停车场"""
        if name in self.parking_lots:
            logger.warning(f"停车场 {name} 已存在")
            return False
            
        self.parking_lots[name] = ParkingLot(name, total_spaces)
        logger.info(f"创建停车场: {name}, 总车位: {total_spaces}")
        return True
    
    def register_vehicle(self, plate_number: str, vehicle_type: str, 
                        owner_info: Dict = None, monthly_fee: float = None) -> bool:
        """注册车辆"""
        if plate_number in self.vehicle_registry:
            logger.warning(f"车牌号 {plate_number} 已注册")
            return False
            
        self.vehicle_registry[plate_number] = {
            "vehicle_type": vehicle_type,
            "owner_info": owner_info or {},
            "monthly_fee": monthly_fee,
            "registration_date": datetime.now().isoformat(),
            "balance": 0.0 if vehicle_type == VehicleType.PREPAID else None
        }
        
        logger.info(f"注册车辆: {plate_number}, 类型: {vehicle_type}")
        return True
    
    def add_balance(self, plate_number: str, amount: float) -> bool:
        """为储值车充值"""
        if plate_number not in self.vehicle_registry:
            logger.warning(f"车牌号 {plate_number} 未注册")
            return False
            
        vehicle_info = self.vehicle_registry[plate_number]
        if vehicle_info["vehicle_type"] != VehicleType.PREPAID:
            logger.warning(f"车牌号 {plate_number} 不是储值车")
            return False
            
        vehicle_info["balance"] += amount
        logger.info(f"为车牌号 {plate_number} 充值 ¥{amount:.2f}")
        return True
    
    def deduct_balance(self, plate_number: str, amount: float) -> bool:
        """从储值车扣费"""
        if plate_number not in self.vehicle_registry:
            return False
            
        vehicle_info = self.vehicle_registry[plate_number]
        if vehicle_info["vehicle_type"] != VehicleType.PREPAID:
            return False
            
        if vehicle_info["balance"] < amount:
            logger.warning(f"车牌号 {plate_number} 余额不足")
            return False
            
        vehicle_info["balance"] -= amount
        return True
    
    def get_vehicle_registry_info(self, plate_number: str) -> Optional[Dict]:
        """获取车辆注册信息"""
        return self.vehicle_registry.get(plate_number)
    
    def get_system_summary(self) -> Dict:
        """获取系统总览"""
        total_revenue = sum(lot.get_total_revenue() for lot in self.parking_lots.values())
        total_vehicles = sum(lot.occupied_spaces for lot in self.parking_lots.values())
        
        return {
            "total_parking_lots": len(self.parking_lots),
            "total_vehicles": total_vehicles,
            "total_revenue": total_revenue,
            "registered_vehicles": len(self.vehicle_registry)
        }

def main():
    """主函数 - 演示系统功能"""
    print("=== 停车场管理系统演示 ===\n")
    
    # 创建停车场管理系统
    system = ParkingSystem()
    
    # 创建停车场
    system.create_parking_lot("主停车场", 100)
    system.create_parking_lot("地下停车场", 50)
    
    # 注册车辆
    system.register_vehicle("京A12345", VehicleType.MONTHLY, {"owner": "张三", "phone": "13800138000"})
    system.register_vehicle("京B67890", VehicleType.PREPAID, {"owner": "李四", "phone": "13900139000"})
    system.register_vehicle("京C11111", VehicleType.FREE, {"owner": "王五", "phone": "13700137000"})
    
    # 为储值车充值
    system.add_balance("京B67890", 500.0)
    
    # 获取主停车场
    main_lot = system.parking_lots["主停车场"]
    
    # 车辆入场
    print("=== 车辆入场 ===")
    main_lot.enter_parking("京A12345", VehicleType.MONTHLY)
    main_lot.enter_parking("京B67890", VehicleType.PREPAID)
    main_lot.enter_parking("京C11111", VehicleType.FREE)
    
    # 模拟停车时间
    import time
    print("\n模拟停车2小时...")
    time.sleep(1)  # 实际演示时可以调整
    
    # 车辆离场
    print("\n=== 车辆离场 ===")
    fee1 = main_lot.exit_parking("京A12345")
    fee2 = main_lot.exit_parking("京B67890")
    fee3 = main_lot.exit_parking("京C11111")
    
    # 显示结果
    print(f"\n=== 收费结果 ===")
    print(f"月租车(京A12345): ¥{fee1:.2f}")
    print(f"储值车(京B67890): ¥{fee2:.2f}")
    print(f"免费车(京C11111): ¥{fee3:.2f}")
    
    # 显示停车场状态
    print(f"\n=== 停车场状态 ===")
    status = main_lot.get_parking_status()
    for key, value in status.items():
        print(f"{key}: {value}")
    
    # 显示统计信息
    print(f"\n=== 统计信息 ===")
    stats = main_lot.get_statistics()
    for vehicle_type, data in stats.items():
        print(f"{vehicle_type}: 数量={data['count']}, 收入=¥{data['revenue']:.2f}")
    
    # 显示系统总览
    print(f"\n=== 系统总览 ===")
    summary = system.get_system_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()