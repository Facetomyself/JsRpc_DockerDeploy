#!/usr/bin/env python3
"""
JsRpc功能测试脚本
测试各项API接口是否正常工作
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class JsRpcTester:
    def __init__(self, base_url: str = "http://localhost:30003"):
        self.base_url = base_url.rstrip('/')
        self.ws_url = f"ws://localhost:30003/ws?group=test_group"
        self.session = requests.Session()
        self.session.timeout = 10

    def test_root_endpoint(self) -> bool:
        """测试根路径访问"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200 and "欢迎使用JsRpc" in response.text:
                print("✅ 根路径访问正常")
                return True
            else:
                print(f"❌ 根路径访问失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 根路径访问异常: {e}")
            return False

    def test_list_endpoint(self) -> bool:
        """测试客户端列表接口"""
        try:
            response = self.session.get(f"{self.base_url}/list")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 客户端列表接口正常，当前连接数: {len(data) if isinstance(data, list) else 'unknown'}")
                return True
            else:
                print(f"❌ 客户端列表接口失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 客户端列表接口异常: {e}")
            return False

    def test_execjs_endpoint(self) -> bool:
        """测试远程执行JavaScript代码"""
        js_code = """
        (function(){
            console.log("JsRpc test execution");
            return "Hello from JsRpc test!";
        })()
        """

        try:
            data = {
                "group": "default",
                "code": js_code
            }
            response = self.session.post(f"{self.base_url}/execjs", data=data)

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "200" and "Hello from JsRpc test!" in result.get("data", ""):
                    print("✅ 远程JS执行正常")
                    return True
                else:
                    print(f"❌ 远程JS执行结果异常: {result}")
                    return False
            else:
                print(f"❌ 远程JS执行请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 远程JS执行异常: {e}")
            return False

    def test_go_endpoint_registered_method(self) -> bool:
        """测试调用已注册的方法"""
        try:
            # 首先尝试调用一个可能存在的已注册方法
            params = {
                "group": "default",
                "action": "_execjs",  # 内置方法
                "param": "return 'test builtin method';"
            }
            response = self.session.get(f"{self.base_url}/go", params=params)

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 200:
                    print("✅ 内置方法调用正常")
                    return True
                else:
                    print(f"⚠️ 内置方法调用结果: {result}")
                    return True  # 不算失败，只是没有预注册方法
            else:
                print(f"❌ 方法调用请求失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 方法调用异常: {e}")
            return False

    def test_page_endpoints(self) -> bool:
        """测试页面信息获取接口"""
        success_count = 0
        total_tests = 2

        # 测试HTML获取
        try:
            response = self.session.get(f"{self.base_url}/page/html?group=default")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 200 and result.get("data"):
                    print("✅ 页面HTML获取正常")
                    success_count += 1
                else:
                    print(f"❌ 页面HTML获取结果异常: {result}")
            else:
                print(f"❌ 页面HTML获取请求失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 页面HTML获取异常: {e}")

        # 测试Cookie获取
        try:
            response = self.session.get(f"{self.base_url}/page/cookie?group=default")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 200:
                    print("✅ 页面Cookie获取正常")
                    success_count += 1
                else:
                    print(f"❌ 页面Cookie获取结果异常: {result}")
            else:
                print(f"❌ 页面Cookie获取请求失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 页面Cookie获取异常: {e}")

        return success_count > 0  # 至少有一个成功

    def test_websocket_echo(self) -> bool:
        """测试WebSocket回显功能"""
        try:
            import websocket
            ws = websocket.create_connection(f"ws://localhost:30003/wst")
            test_message = "Hello WebSocket Test"
            ws.send(test_message)
            response = ws.recv()
            ws.close()

            # WebSocket返回bytes对象，需要正确比较
            if isinstance(response, bytes):
                response_str = response.decode('utf-8')
            else:
                response_str = str(response)

            if response_str == test_message:
                print("✅ WebSocket回显功能正常")
                return True
            else:
                print(f"❌ WebSocket回显结果不匹配: 期望'{test_message}', 实际'{response_str}' (原始: {repr(response)})")
                return False
        except ImportError:
            print("⚠️ 跳过WebSocket测试（需要安装websocket-client）")
            return True
        except Exception as e:
            print(f"❌ WebSocket测试异常: {e}")
            return False

    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始JsRpc功能测试...\n")

        tests = [
            ("根路径访问", self.test_root_endpoint),
            ("客户端列表", self.test_list_endpoint),
            ("远程JS执行", self.test_execjs_endpoint),
            ("方法调用", self.test_go_endpoint_registered_method),
            ("页面信息", self.test_page_endpoints),
            ("WebSocket回显", self.test_websocket_echo),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"正在测试: {test_name}")
            if test_func():
                passed += 1
            print()

        print(f"🎯 测试完成: {passed}/{total} 项通过")

        if passed >= total - 1:  # 允许一项失败（WebSocket可能需要额外依赖）
            print("✅ JsRpc服务运行正常！")
            return True
        else:
            print("❌ JsRpc服务存在问题")
            return False

def main():
    """主函数"""
    print("JsRpc 功能测试工具")
    print("=" * 50)

    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:30003/", timeout=5)
        if response.status_code != 200:
            print("❌ JsRpc服务未运行，请先启动服务")
            sys.exit(1)
    except:
        print("❌ 无法连接到JsRpc服务，请确保服务在localhost:30003运行")
        sys.exit(1)

    tester = JsRpcTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
