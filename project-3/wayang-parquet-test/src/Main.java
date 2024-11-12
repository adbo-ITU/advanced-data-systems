import org.apache.wayang.api.JavaPlanBuilder;
import org.apache.wayang.basic.data.Tuple2;
import org.apache.wayang.core.api.WayangContext;
import org.apache.wayang.java.Java;

import java.util.Arrays;
import java.util.Collection;

public class Main {
    public static void main(String[] args) {
        String path = "file:///Users/adrian/coding/advanced-data-systems/project-3/wayang-parquet-test/testFile.txt";

        WayangContext wayangContext = new WayangContext();
        wayangContext.register(Java.basicPlugin());

        JavaPlanBuilder planBuilder = new JavaPlanBuilder(wayangContext)
                .withJobName("ParquetVroom")
                .withUdfJarOf(Main.class);

        Collection<Tuple2<String, Integer>> wordcounts = planBuilder
                .readTextFile(path).withName("Load file")

                /* Split each line by non-word characters */
                .flatMap(line -> Arrays.asList(line.split("\\W+")))
                .withSelectivity(1, 100, 0.9)
                .withName("Split words")

                /* Filter empty tokens */
                .filter(token -> !token.isEmpty())
                .withName("Filter empty words")

                /* Attach counter to each word */
                .map(word -> new Tuple2<>(word.toLowerCase(), 1)).withName("To lower case, add counter")

                // Sum up counters for every word.
                .reduceByKey(
                        Tuple2::getField0,
                        (t1, t2) -> new Tuple2<>(t1.getField0(), t1.getField1() + t2.getField1())
                )
                .withName("Add counters")

                /* Execute the plan and collect the results */
                .collect();


        System.out.printf("Found %d words:\n", wordcounts.size());
        wordcounts.forEach(wc -> System.out.printf("%dx %s\n", wc.field1, wc.field0));
    }
}