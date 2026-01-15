"""
이메일 알림 시스템
가격 변동 및 투자 기회 알림
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from typing import List, Dict
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """이메일 알림 관리 클래스"""
    
    def __init__(self):
        # Gmail SMTP 설정
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('EMAIL_ADDRESS')
        self.sender_password = os.getenv('EMAIL_PASSWORD')  # Gmail 앱 비밀번호
        
        if not self.sender_email or not self.sender_password:
            logger.warning("이메일 설정이 없습니다. .env 파일을 확인하세요.")
    
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        이메일 발송
        
        Args:
            to_email: 수신자 이메일
            subject: 제목
            html_content: HTML 내용
        
        Returns:
            bool: 성공 여부
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email
            
            # HTML 파트 추가
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"이메일 발송 성공: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 발송 실패: {str(e)}")
            return False
    
    def send_price_drop_alert(
        self, 
        user_email: str, 
        complex_name: str, 
        area_type: str,
        old_price: float, 
        new_price: float,
        price_type: str = "매매가"
    ) -> bool:
        """
        가격 하락 알림
        
        Args:
            user_email: 사용자 이메일
            complex_name: 아파트명
            area_type: 면적 타입
            old_price: 이전 가격 (억)
            new_price: 현재 가격 (억)
            price_type: 가격 유형 (매매가/전세가)
        
        Returns:
            bool: 성공 여부
        """
        change = new_price - old_price
        change_percent = (change / old_price * 100) if old_price > 0 else 0
        
        subject = f"🔔 {complex_name} {price_type} 하락 알림"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
                <h2 style="color: #E53935;">🔔 가격 하락 알림</h2>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #333;">{complex_name}</h3>
                    <p style="font-size: 14px; color: #666;">{area_type}</p>
                    
                    <div style="margin: 20px 0;">
                        <p style="margin: 5px 0;">
                            <strong>이전 {price_type}:</strong> 
                            <span style="font-size: 18px;">{old_price:.1f}억원</span>
                        </p>
                        <p style="margin: 5px 0;">
                            <strong>현재 {price_type}:</strong> 
                            <span style="font-size: 20px; color: #E53935; font-weight: bold;">
                                {new_price:.1f}억원
                            </span>
                        </p>
                        <p style="margin: 5px 0;">
                            <strong>변동:</strong> 
                            <span style="color: #E53935; font-weight: bold;">
                                {change:.1f}억원 ({change_percent:.1f}%)
                            </span>
                        </p>
                    </div>
                </div>
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    이 알림은 관심 단지의 가격 변동을 자동으로 감지하여 발송되었습니다.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_gap_opportunity_alert(
        self,
        user_email: str,
        complex_name: str,
        area_type: str,
        sale_price: float,
        lease_price: float,
        gap: float
    ) -> bool:
        """
        갭투자 기회 알림
        
        Args:
            user_email: 사용자 이메일
            complex_name: 아파트명
            area_type: 면적 타입
            sale_price: 매매가 (억)
            lease_price: 전세가 (억)
            gap: 갭 (억)
        
        Returns:
            bool: 성공 여부
        """
        lease_rate = (lease_price / sale_price * 100) if sale_price > 0 else 0
        
        subject = f"💰 {complex_name} 갭투자 기회 알림"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; border-radius: 10px;">
                <h2 style="color: #4CAF50;">💰 갭투자 기회 발견!</h2>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #333;">{complex_name}</h3>
                    <p style="font-size: 14px; color: #666;">{area_type}</p>
                    
                    <div style="margin: 20px 0;">
                        <p style="margin: 5px 0;">
                            <strong>매매가:</strong> 
                            <span style="font-size: 18px;">{sale_price:.1f}억원</span>
                        </p>
                        <p style="margin: 5px 0;">
                            <strong>전세가:</strong> 
                            <span style="font-size: 18px;">{lease_price:.1f}억원</span>
                        </p>
                        <p style="margin: 5px 0;">
                            <strong>투자금(갭):</strong> 
                            <span style="font-size: 22px; color: #4CAF50; font-weight: bold;">
                                {gap:.1f}억원
                            </span>
                        </p>
                        <p style="margin: 5px 0;">
                            <strong>전세가율:</strong> 
                            <span style="font-size: 16px;">
                                {lease_rate:.1f}%
                            </span>
                        </p>
                    </div>
                </div>
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    설정한 투자금 조건에 맞는 매물입니다.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_test_email(self, to_email: str) -> bool:
        """테스트 이메일 발송"""
        subject = "🧪 네이버 부동산 분석 - 테스트 이메일"
        html_content = """
        <html>
        <body>
            <h2>테스트 이메일</h2>
            <p>이메일 알림 시스템이 정상적으로 작동합니다!</p>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html_content)
