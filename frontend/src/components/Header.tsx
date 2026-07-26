import React from 'react';
import '../styles/Header.css';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-left">
        {/* Can be breadcrumbs or session title */}
      </div>
      <div className="header-right">
        <div className="tenant-profile">
          <span className="tenant-name">Acme Corp Sales</span>
          <div className="avatar">A</div>
        </div>
      </div>
    </header>
  );
};

export default Header;
