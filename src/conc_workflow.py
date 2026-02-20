from pathlib import Path
from rel_check import rel_check
import time
from workflows.retry_policy import ConstantDelayRetryPolicy
from llama_index.core.workflow import (
    step,
    Context,
    Workflow,
    Event,
    StartEvent,
    StopEvent,
)


class ProcessEvent(Event):
    filename: str


class ResultEvent(Event):
    result: dict[str, str]


class ConcurrentWorkflow(Workflow):
    def __init__(self, prompt: str, *args, **kwargs):
        self.prompt = prompt
        super().__init__(*args, **kwargs)

    # Returns a list of files in a directory
    @staticmethod
    def get_filenames(directory_path):
        path = Path(directory_path)
        return [directory_path + f.name for f in path.iterdir() if f.is_file()]

    # Looks at a dictionary, the Value is either Yes or No
    # Returns True if the Value is Yes
    @staticmethod
    def is_relevant(input: dict[str, str]):
        for x, y in input.items():
            if y == "Yes":
                return True
            elif y == "No":
                return False
            else:
                return None

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> ProcessEvent:
        data_list = ConcurrentWorkflow.get_filenames('data/')
        await ctx.store.set("num_to_collect", len(data_list))
        for item in data_list:
            print(f"Sending {item} to ProcessEvent")
            ctx.send_event(
                ProcessEvent(filename=item)
            )
        return None

    @step(num_workers=2,
          retry_policy=ConstantDelayRetryPolicy(delay=2, maximum_attempts=3)
          )
    async def process_data(self, ev: ProcessEvent) -> ResultEvent:
        print(f"Starting relevancy check on {ev.filename}")
        start = time.perf_counter()
        # Asynchronously performs relevancy check operation
        output = await rel_check(
                prompt=self.prompt,
                file_name=ev.filename)
        end = time.perf_counter()
        print(f"Finished relevancy check on {ev.filename} \
            in {end - start:.2f} seconds.")
        return ResultEvent(result=output)

    @step
    async def combine_results(
        self,
        ctx: Context,
        ev: ResultEvent
    ) -> StopEvent | None:
        num_to_collect = await ctx.store.get("num_to_collect")
        # Combines outputs from the process_data() calls into 1 return value
        results = ctx.collect_events(ev, [ResultEvent] * num_to_collect)
        if results is None:
            return None
        # Takes the combined output and creates data structures needed later
        rel_list = []
        non_rel_list = []
        for event in results:
            for k, v in event.result.items():
                if ConcurrentWorkflow.is_relevant(event.result):
                    rel_list.append(k)
                elif not ConcurrentWorkflow.is_relevant(event.result):
                    non_rel_list.append(k)
        # Returns 2 lists of strings containing the filenames.
        # First list is the list of files that are relevant to the prompt.
        # Second list are files not relevant to the prompt
        if len(rel_list) == 0:
            rel_list.append("No Relevant Results")
        if len(non_rel_list) == 0:
            non_rel_list.append("No Non-Relevant Results")
        results = [rel_list, non_rel_list]
        return StopEvent(result=results)
