import React from 'react';
import styles from './Loading.module.css';

const Loading = () => {
  return (
    <div className={styles.loadingContainer}>
     
      <div className={styles.loadingDotsContainer}>
        <div className={styles.loadingDots}></div>
        <div className={styles.loadingDots}></div>
        <div className={styles.loadingDots}></div>
      </div>
      {/* <p>Loading...</p> */}
    </div>
  );
};

export default Loading;