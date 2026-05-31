import { StatePanel } from "@/components/ui/StatePanel";
import { FetResearchPage } from "@/features/fet-research/FetResearchPage";
import { useTokenPage } from "@/hooks/useTokenPage";

export default function Home() {
  const { data, isLoading, error } = useTokenPage();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10 xl:px-0">
        <StatePanel
          title="正在加载 FET 研究页面"
          description="前端当前通过只读 API 获取页面聚合数据，图表、地址表和 AI 画像会在同一份页面模型中返回。"
        />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10 xl:px-0">
        <StatePanel
          title="页面数据暂时不可用"
          description={error ?? "未读取到 FET 页面数据，请检查后端 API 是否已启动。"}
          variant="error"
        />
      </div>
    );
  }

  return <FetResearchPage data={data} />;
}
