import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

const MarkdownViewer = ({ markdownText }) => {
  return (
    <div className="prose prose-sm md:prose-base lg:prose-lg dark:prose-invert max-w-none">
      <ReactMarkdown
        children={markdownText}
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
      />
    </div>
  );
};

export default MarkdownViewer;
