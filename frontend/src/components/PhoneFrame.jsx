// 폰 베젤 + 노치. 내용물(채팅 앱)은 children 으로.
export default function PhoneFrame({ children }) {
  return (
    <div className="phone">
      <div className="phone-screen">
        <div className="notch" />
        {children}
      </div>
    </div>
  );
}
